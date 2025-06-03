"""
Flask web app for control and dashboard.
Provides start/stop motion control and displays latest images.
"""

from flask import Flask, render_template, jsonify, request
import threading
import time
from motor_control import MotorControl
from sensors import MPU6050, UltrasonicSensor
from autonomous_logic import AutonomousLogic

app = Flask(__name__)

motion_running = False
motion_thread = None

# Initialize hardware components
motor_control = MotorControl()
mpu6050 = MPU6050()
front_sensor = UltrasonicSensor(trigger_pin=5, echo_pin=6)  # Example GPIO pins
back_sensor = UltrasonicSensor(trigger_pin=13, echo_pin=19)
bottom_sensor = UltrasonicSensor(trigger_pin=20, echo_pin=21)

autonomous_logic = AutonomousLogic(motor_control, mpu6050, front_sensor, back_sensor, bottom_sensor)

def autonomous_run():
    global motion_running
    while motion_running:
        autonomous_logic.run()
        time.sleep(1)

@app.route('/')
def index():
    # Render dashboard page
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start_motion():
    global motion_running, motion_thread
    if not motion_running:
        motion_running = True
        motion_thread = threading.Thread(target=autonomous_run)
        motion_thread.start()
    return jsonify({'status': 'started'})

@app.route('/stop', methods=['POST'])
def stop_motion():
    global motion_running, motion_thread
    if motion_running:
        motion_running = False
        motion_thread.join()
        motor_control.stop()
    return jsonify({'status': 'stopped'})

@app.route('/status')
def status():
    return jsonify({'motion_running': motion_running})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
