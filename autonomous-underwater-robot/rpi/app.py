"""
Flask web app for control and dashboard.
Provides start/stop motion control and displays latest images.
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import threading
import time
import os
import glob
import logging
from motor_control import MotorControl
from sensors import MPU6050, UltrasonicSensor
from autonomous_logic import AutonomousLogic

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for web dashboard

motion_running = False
motion_thread = None

# Configuration
IMAGE_DIRECTORY = "/path/to/esp32/images"  # Update this path to match ESP32-CAM SD card mount point
MAX_IMAGES = 5

try:
    # Initialize hardware components
    motor_control = MotorControl()
    mpu6050 = MPU6050()
    front_sensor = UltrasonicSensor(trigger_pin=5, echo_pin=25)
    back_sensor = UltrasonicSensor(trigger_pin=7, echo_pin=8)
    bottom_sensor = UltrasonicSensor(trigger_pin=20, echo_pin=21)
    
    autonomous_logic = AutonomousLogic(motor_control, mpu6050, front_sensor, back_sensor, bottom_sensor)
    logger.info("Hardware components initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize hardware: {e}")
    # Create mock objects for development/testing
    motor_control = None
    autonomous_logic = None

def autonomous_run():
    """Run autonomous logic in a separate thread"""
    global motion_running
    try:
        while motion_running:
            if autonomous_logic:
                autonomous_logic.run()
            time.sleep(1)
    except Exception as e:
        logger.error(f"Error in autonomous run: {e}")
        motion_running = False

def get_latest_images():
    """Get the latest images from ESP32-CAM"""
    try:
        if not os.path.exists(IMAGE_DIRECTORY):
            logger.warning(f"Image directory {IMAGE_DIRECTORY} does not exist")
            return []
        
        # Get all jpg files and sort by modification time
        image_files = glob.glob(os.path.join(IMAGE_DIRECTORY, "*.jpg"))
        image_files.sort(key=os.path.getmtime, reverse=True)
        
        # Return the latest MAX_IMAGES files
        latest_images = image_files[:MAX_IMAGES]
        
        # Convert to relative paths for web serving
        return [os.path.basename(img) for img in latest_images]
    except Exception as e:
        logger.error(f"Error getting latest images: {e}")
        return []

@app.route('/')
def index():
    """Render dashboard page"""
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start_motion():
    """Start autonomous motion control"""
    global motion_running, motion_thread
    try:
        if not motion_running and autonomous_logic:
            motion_running = True
            motion_thread = threading.Thread(target=autonomous_run)
            motion_thread.daemon = True
            motion_thread.start()
            logger.info("Motion control started")
            return jsonify({'status': 'started', 'success': True})
        elif not autonomous_logic:
            return jsonify({'status': 'error', 'message': 'Hardware not initialized', 'success': False}), 500
        else:
            return jsonify({'status': 'already_running', 'success': True})
    except Exception as e:
        logger.error(f"Error starting motion: {e}")
        return jsonify({'status': 'error', 'message': str(e), 'success': False}), 500

@app.route('/stop', methods=['POST'])
def stop_motion():
    """Stop autonomous motion control"""
    global motion_running, motion_thread
    try:
        if motion_running:
            motion_running = False
            if motion_thread and motion_thread.is_alive():
                motion_thread.join(timeout=5)
            if motor_control:
                motor_control.stop()
            logger.info("Motion control stopped")
            return jsonify({'status': 'stopped', 'success': True})
        else:
            return jsonify({'status': 'already_stopped', 'success': True})
    except Exception as e:
        logger.error(f"Error stopping motion: {e}")
        return jsonify({'status': 'error', 'message': str(e), 'success': False}), 500

@app.route('/status')
def status():
    """Get current robot status"""
    try:
        return jsonify({
            'motion_running': motion_running,
            'hardware_initialized': autonomous_logic is not None,
            'success': True
        })
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({'status': 'error', 'message': str(e), 'success': False}), 500

@app.route('/images')
def images():
    """Get latest captured images"""
    try:
        latest_images = get_latest_images()
        return jsonify({
            'images': latest_images,
            'count': len(latest_images),
            'success': True
        })
    except Exception as e:
        logger.error(f"Error getting images: {e}")
        return jsonify({'images': [], 'count': 0, 'success': False, 'message': str(e)})

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found', 'success': False}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error', 'success': False}), 500

if __name__ == '__main__':
    logger.info("Starting Flask application...")
    app.run(host='0.0.0.0', port=5000, debug=True)
