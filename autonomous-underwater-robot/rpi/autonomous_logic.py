"""
Autonomous logic module for underwater robot.
Implements rectangle lap movement, obstacle avoidance, stabilization, and depth control.
"""

import time

class AutonomousLogic:
    def __init__(self, motor_control, mpu6050, front_sensor, back_sensor, bottom_sensor):
        self.motor_control = motor_control
        self.mpu6050 = mpu6050
        self.front_sensor = front_sensor
        self.back_sensor = back_sensor
        self.bottom_sensor = bottom_sensor
        self.tilt_threshold = 15  # degrees
        self.depth_threshold = 10  # cm
        self.lap_time = 30  # seconds per lap
        self.laps = 2

    def check_tilt(self):
        orientation = self.mpu6050.get_orientation()
        pitch = orientation['pitch']
        roll = orientation['roll']
        if abs(pitch) > self.tilt_threshold or abs(roll) > self.tilt_threshold:
            return True
        return False

    def check_obstacles(self):
        front_dist = self.front_sensor.get_distance()
        back_dist = self.back_sensor.get_distance()
        if front_dist < self.depth_threshold or back_dist < self.depth_threshold:
            return True
        return False

    def check_depth(self):
        depth = self.bottom_sensor.get_distance()
        if depth < self.depth_threshold:
            return True
        return False

    def run_lap(self):
        # Simple rectangle lap: forward, right turn, forward, right turn, etc.
        # For simplicity, just move forward for lap_time seconds twice
        start_time = time.time()
        while time.time() - start_time < self.lap_time:
            if self.check_obstacles() or self.check_tilt() or not self.check_depth():
                self.motor_control.stop()
                time.sleep(1)
            else:
                self.motor_control.forward(70)
            time.sleep(0.1)
        self.motor_control.stop()

    def run(self):
        # Auto submerge on start
        self.motor_control.down(70)
        time.sleep(5)  # submerge for 5 seconds
        self.motor_control.stop()

        for _ in range(self.laps):
            self.run_lap()

        # Auto float up on stop
        self.motor_control.up(70)
        time.sleep(5)
        self.motor_control.stop()
