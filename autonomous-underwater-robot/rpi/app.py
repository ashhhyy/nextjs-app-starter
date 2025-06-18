"""
Flask web app for control and dashboard.
Provides start/stop motion control and displays latest images from ESP32-CAM.
"""

from flask import Flask, jsonify, request, send_from_directory # Added send_from_directory
from flask_cors import CORS
import threading
import time
import os
import logging
# import glob # Not strictly needed if managing images via list, but can keep for other uses

# Hardware imports - ensure these modules exist and work correctly
# If any of these imports fail, the corresponding hardware functionality
# will be disabled, but the web server will still run.
try:
    from motor_control import MotorControl
    from sensors import MPU6050, UltrasonicSensor
    from autonomous_logic import AutonomousLogic
    HARDWARE_INITIALIZED = True
except ImportError as e:
    # Log the error and set a flag so Flask knows hardware isn't ready
    logging.getLogger(__name__).error(f"Hardware import failed: {e}. Running in mock mode.")
    HARDWARE_INITIALIZED = False
except Exception as e:
    logging.getLogger(__name__).error(f"Error during hardware module import: {e}. Running in mock mode.")
    HARDWARE_INITIALIZED = False


# --- Configure Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Flask App Initialization ---
app = Flask(__name__)
CORS(app) # Enable CORS for web dashboard. This is crucial for cross-origin requests from your browser.

# --- Global State Variables ---
motion_running = False # Tracks if autonomous motion is active
motion_thread = None   # Thread for autonomous logic
latest_images = []     # List to store URLs/paths of the latest images for the dashboard
MAX_IMAGES_TO_DISPLAY = 5 # Number of latest images to keep in memory for the dashboard

# --- Directory for Image Storage ---
# This path points to the 'images' directory in the root of your project
# e.g., ~/nextjs-app-starter/autonomous-underwater-robot/images
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, 'images')

# Ensure the upload directory exists
try:
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    logger.info(f"Image upload directory ensured: {UPLOAD_FOLDER}")
except OSError as e:
    logger.error(f"Failed to create image upload directory {UPLOAD_FOLDER}: {e}")

# --- Hardware Initialization (Conditional) ---
motor_control = None
mpu6050 = None
front_sensor = None
back_sensor = None
bottom_sensor = None
autonomous_logic = None

if HARDWARE_INITIALIZED:
    try:
        motor_control = MotorControl()
        mpu6050 = MPU6050()
        # Ensure pin numbers here match your physical connections for UltrasonicSensor
        front_sensor = UltrasonicSensor(trigger_pin=5, echo_pin=25)
        back_sensor = UltrasonicSensor(trigger_pin=7, echo_pin=8)
        bottom_sensor = UltrasonicSensor(trigger_pin=20, echo_pin=21)
        
        autonomous_logic = AutonomousLogic(motor_control, mpu6050, front_sensor, back_sensor, bottom_sensor)
        logger.info("Hardware components initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize hardware components: {e}. Running in mock mode.")
        HARDWARE_INITIALIZED = False # Set to False if any component fails to initialize


# --- Autonomous Logic Thread Function ---
def autonomous_run():
    """Runs autonomous logic in a separate thread."""
    global motion_running
    logger.info("Autonomous motion thread started.")
    try:
        while motion_running:
            if autonomous_logic:
                autonomous_logic.run()
            else:
                logger.warning("Autonomous logic is not initialized. Skipping run cycle.")
                time.sleep(1) # Still sleep to prevent busy-looping if not initialized
            time.sleep(1) # Control loop delay
    except Exception as e:
        logger.error(f"Critical error in autonomous run thread: {e}")
        motion_running = False # Stop motion on error
        if motor_control:
            motor_control.stop() # Ensure motors stop on error
    finally:
        logger.info("Autonomous motion thread stopped.")


# --- API Endpoints ---

@app.route('/')
def hello_world():
    """Simple root endpoint for testing Flask server connectivity."""
    return "Autonomous Underwater Robot API is running!"

@app.route('/status', methods=['GET'])
def get_status():
    """Returns the current motion status of the robot and hardware initialization status."""
    try:
        return jsonify({
            'motion_running': motion_running,
            'hardware_initialized': HARDWARE_INITIALIZED,
            'success': True
        })
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({'status': 'error', 'message': str(e), 'success': False}), 500

@app.route('/start', methods=['POST'])
def start_motion():
    """Starts the autonomous motion control."""
    global motion_running, motion_thread
    try:
        if not HARDWARE_INITIALIZED:
            return jsonify({'status': 'error', 'message': 'Hardware not initialized. Cannot start motion.', 'success': False}), 500
            
        if not motion_running:
            motion_running = True
            motion_thread = threading.Thread(target=autonomous_run)
            motion_thread.daemon = True # Allow main program to exit even if thread is running
            motion_thread.start()
            logger.info("Motion control started.")
            return jsonify({'status': 'started', 'success': True})
        else:
            return jsonify({'status': 'already_running', 'success': True})
    except Exception as e:
        logger.error(f"Error starting motion: {e}")
        return jsonify({'status': 'error', 'message': str(e), 'success': False}), 500

@app.route('/stop', methods=['POST'])
def stop_motion():
    """Stops the autonomous motion control."""
    global motion_running, motion_thread
    try:
        if motion_running:
            motion_running = False
            # Wait for the thread to finish cleanly (up to 5 seconds)
            if motion_thread and motion_thread.is_alive():
                motion_thread.join(timeout=5)
                if motion_thread.is_alive():
                    logger.warning("Motion thread did not terminate cleanly after 5 seconds.")
            
            if motor_control: # Ensure motors are stopped if control is available
                motor_control.stop()
            logger.info("Motion control stopped.")
            return jsonify({'status': 'stopped', 'success': True})
        else:
            return jsonify({'status': 'already_stopped', 'success': True})
    except Exception as e:
        logger.error(f"Error stopping motion: {e}")
        return jsonify({'status': 'error', 'message': str(e), 'success': False}), 500

@app.route('/upload_image', methods=['POST'])
def upload_image():
    """
    Receives image data from ESP32-CAM and saves it.
    Updates the list of latest images for the web dashboard.
    """
    global latest_images
    image_data = None
    
    # Check if content type is 'image/jpeg' for raw binary upload (preferred for ESP32-CAM)
    if request.content_type == 'image/jpeg':
        image_data = request.get_data()
        if not image_data:
            logger.warning("No raw image data received in POST request.")
            return jsonify({"error": "No image data received"}), 400
    # Fallback: Check for multipart/form-data with a file field named 'image'
    elif 'image' in request.files:
        image_file = request.files['image']
        if image_file.filename == '':
            logger.warning("Received multipart form data but no file selected.")
            return jsonify({"error": "No selected file"}), 400
        image_data = image_file.read()
    else:
        logger.warning(f"Unsupported Content-Type for image upload: {request.content_type}")
        return jsonify({"error": "No image part or unsupported content type"}), 400

    # Generate a unique filename using timestamp
    # Ensure this doesn't conflict with existing filenames if you also scan from ESP32 SD card
    filename = f"esp32_cam_{int(time.time())}.jpg"
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    try:
        with open(filepath, 'wb') as f:
            f.write(image_data)
        
        # Construct URL relative to the Flask server's image serving endpoint
        # e.g., /images/esp32_cam_1678886400.jpg
        image_url = f"/images/{filename}" 
        
        # Add the new image URL to the front of the list
        latest_images.insert(0, image_url) 
        
        # Maintain the maximum number of images to display
        if len(latest_images) > MAX_IMAGES_TO_DISPLAY:
            # Optionally, you could delete the actual oldest file from disk here
            # os.remove(os.path.join(UPLOAD_FOLDER, os.path.basename(latest_images.pop())))
            latest_images.pop() # Just remove from the list for now

        logger.info(f"Image uploaded and saved to: {filepath}")
        return jsonify({"message": "Image uploaded successfully", "filename": filename, "url": image_url}), 200
    except Exception as e:
        logger.error(f"Error saving uploaded image to disk: {e}")
        return jsonify({"error": f"Failed to save image: {e}"}), 500

@app.route('/images/<filename>', methods=['GET'])
def serve_image(filename):
    """
    Serves static image files from the UPLOAD_FOLDER to the web dashboard.
    """
    try:
        return send_from_directory(UPLOAD_FOLDER, filename)
    except FileNotFoundError:
        logger.error(f"Image file not found: {filename}")
        return jsonify({"error": "Image not found"}), 404
    except Exception as e:
        logger.error(f"Error serving image {filename}: {e}")
        return jsonify({"error": "Failed to serve image"}), 500

@app.route('/images', methods=['GET'])
def get_latest_images_for_dashboard():
    """
    Returns the list of URLs for the latest images stored in memory.
    The web dashboard will call this.
    """
    try:
        # Return the list of images URLs that Flask is managing from uploads
        return jsonify({
            'images': latest_images,
            'count': len(latest_images),
            'success': True
        })
    except Exception as e:
        logger.error(f"Error getting latest images list: {e}")
        return jsonify({'images': [], 'count': 0, 'success': False, 'message': str(e)})


# --- Error Handlers ---
@app.errorhandler(404)
def not_found(error):
    logger.warning(f"404 Not Found: {request.path}")
    return jsonify({'error': 'Not found', 'success': False}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.exception("Internal server error occurred.") # Log exception traceback
    return jsonify({'error': 'Internal server error', 'success': False}), 500

# --- Main Run Block ---
if __name__ == '__main__':
    logger.info("Starting Flask application...")
    # This makes the Flask app accessible from any device on the network on port 5000
    app.run(host='0.0.0.0', port=5000, debug=True)
