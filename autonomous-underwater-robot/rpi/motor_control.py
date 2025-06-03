"""
Motor control module for 4 propellers using L298N motor drivers.
Controls 2 motors for forward/backward and 2 motors for up/down movement.
"""

import RPi.GPIO as GPIO
import time

class MotorControl:
    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        # Define GPIO pins for motors
        # Forward/backward motors
        self.FB_IN1 = 17
        self.FB_IN2 = 18
        self.FB_EN = 27
        # Up/down motors
        self.UD_IN1 = 22
        self.UD_IN2 = 23
        self.UD_EN = 24

        # Setup pins
        GPIO.setup(self.FB_IN1, GPIO.OUT)
        GPIO.setup(self.FB_IN2, GPIO.OUT)
        GPIO.setup(self.FB_EN, GPIO.OUT)

        GPIO.setup(self.UD_IN1, GPIO.OUT)
        GPIO.setup(self.UD_IN2, GPIO.OUT)
        GPIO.setup(self.UD_EN, GPIO.OUT)

        # Setup PWM for speed control
        self.fb_pwm = GPIO.PWM(self.FB_EN, 1000)  # 1kHz frequency
        self.ud_pwm = GPIO.PWM(self.UD_EN, 1000)

        self.fb_pwm.start(0)
        self.ud_pwm.start(0)

    def forward(self, speed: int):
        """Move forward at given speed (0-100)"""
        GPIO.output(self.FB_IN1, GPIO.HIGH)
        GPIO.output(self.FB_IN2, GPIO.LOW)
        self.fb_pwm.ChangeDutyCycle(speed)

    def backward(self, speed: int):
        """Move backward at given speed (0-100)"""
        GPIO.output(self.FB_IN1, GPIO.LOW)
        GPIO.output(self.FB_IN2, GPIO.HIGH)
        self.fb_pwm.ChangeDutyCycle(speed)

    def up(self, speed: int):
        """Move up at given speed (0-100)"""
        GPIO.output(self.UD_IN1, GPIO.HIGH)
        GPIO.output(self.UD_IN2, GPIO.LOW)
        self.ud_pwm.ChangeDutyCycle(speed)

    def down(self, speed: int):
        """Move down at given speed (0-100)"""
        GPIO.output(self.UD_IN1, GPIO.LOW)
        GPIO.output(self.UD_IN2, GPIO.HIGH)
        self.ud_pwm.ChangeDutyCycle(speed)

    def stop(self):
        """Stop all motors"""
        self.fb_pwm.ChangeDutyCycle(0)
        self.ud_pwm.ChangeDutyCycle(0)
        GPIO.output(self.FB_IN1, GPIO.LOW)
        GPIO.output(self.FB_IN2, GPIO.LOW)
        GPIO.output(self.UD_IN1, GPIO.LOW)
        GPIO.output(self.UD_IN2, GPIO.LOW)

    def cleanup(self):
        """Cleanup GPIO"""
        self.stop()
        GPIO.cleanup()
