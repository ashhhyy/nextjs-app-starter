"""
Sensor module for MPU6050 gyroscope and ultrasonic sensors.
Provides orientation data and distance measurements.
"""

import smbus
import time
import RPi.GPIO as GPIO
import math

class MPU6050:
    def __init__(self, bus=1, address=0x68):
        self.bus = smbus.SMBus(bus)
        self.address = address
        # Wake up MPU6050
        self.bus.write_byte_data(self.address, 0x6B, 0)
        time.sleep(0.1)

    def read_word(self, reg):
        high = self.bus.read_byte_data(self.address, reg)
        low = self.bus.read_byte_data(self.address, reg+1)
        val = (high << 8) + low
        if val >= 0x8000:
            return -((65535 - val) + 1)
        else:
            return val

    def get_orientation(self):
        """
        Returns orientation data (pitch, roll, yaw) in degrees
        """
        accel_x = self.read_word(0x3B)
        accel_y = self.read_word(0x3D)
        accel_z = self.read_word(0x3F)

        gyro_x = self.read_word(0x43)
        gyro_y = self.read_word(0x45)
        gyro_z = self.read_word(0x47)

        # Calculate pitch and roll from accelerometer data
        pitch = math.degrees(math.atan2(accel_y, math.sqrt(accel_x**2 + accel_z**2)))
        roll = math.degrees(math.atan2(-accel_x, accel_z))
        yaw = 0  # Yaw calculation requires magnetometer or integration of gyro data

        return {'pitch': pitch, 'roll': roll, 'yaw': yaw}

class UltrasonicSensor:
    def __init__(self, trigger_pin, echo_pin):
        self.trigger_pin = trigger_pin
        self.echo_pin = echo_pin
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.trigger_pin, GPIO.OUT)
        GPIO.setup(self.echo_pin, GPIO.IN)

    def get_distance(self):
        """
        Returns distance measurement in cm
        """
        # Send 10us pulse to trigger
        GPIO.output(self.trigger_pin, True)
        time.sleep(0.00001)
        GPIO.output(self.trigger_pin, False)

        start_time = time.time()
        stop_time = time.time()

        # Save start time
        while GPIO.input(self.echo_pin) == 0:
            start_time = time.time()

        # Save arrival time
        while GPIO.input(self.echo_pin) == 1:
            stop_time = time.time()

        # Time difference
        time_elapsed = stop_time - start_time
        # Calculate distance (speed of sound 34300 cm/s)
        distance = (time_elapsed * 34300) / 2

        return distance
