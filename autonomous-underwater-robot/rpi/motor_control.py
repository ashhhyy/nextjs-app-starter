"""
Motor control module for 4 propellers using L298N motor drivers.
Controls 4 motors independently: left/right for movement and front/back for vertical control.
Each L298N driver controls 2 motors using all 4 inputs (IN1-IN4) and both enables (ENA, ENB).
"""

import RPi.GPIO as GPIO
import time

class MotorControl:
    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        
        # L298N #1 - Forward/Backward Motors
        # Motor A (Left)
        self.LEFT_IN1 = 17
        self.LEFT_IN2 = 18
        self.LEFT_ENA = 27
        # Motor B (Right)
        self.RIGHT_IN3 = 16
        self.RIGHT_IN4 = 19
        self.RIGHT_ENB = 26
        
        # L298N #2 - Up/Down Motors
        # Motor A (Front)
        self.FRONT_IN1 = 22
        self.FRONT_IN2 = 23
        self.FRONT_ENA = 24
        # Motor B (Back)
        self.BACK_IN3 = 12
        self.BACK_IN4 = 13
        self.BACK_ENB = 6

        # Setup all GPIO pins
        pins = [
            self.LEFT_IN1, self.LEFT_IN2, self.LEFT_ENA,
            self.RIGHT_IN3, self.RIGHT_IN4, self.RIGHT_ENB,
            self.FRONT_IN1, self.FRONT_IN2, self.FRONT_ENA,
            self.BACK_IN3, self.BACK_IN4, self.BACK_ENB
        ]
        
        for pin in pins:
            GPIO.setup(pin, GPIO.OUT)

        # Setup PWM for speed control (1kHz frequency)
        self.left_pwm = GPIO.PWM(self.LEFT_ENA, 1000)
        self.right_pwm = GPIO.PWM(self.RIGHT_ENB, 1000)
        self.front_pwm = GPIO.PWM(self.FRONT_ENA, 1000)
        self.back_pwm = GPIO.PWM(self.BACK_ENB, 1000)

        # Start all PWM with 0% duty cycle
        self.left_pwm.start(0)
        self.right_pwm.start(0)
        self.front_pwm.start(0)
        self.back_pwm.start(0)

    def forward(self, speed: int):
        """Move forward at given speed (0-100) - both left and right motors"""
        self._set_motor(self.LEFT_IN1, self.LEFT_IN2, self.left_pwm, True, speed)
        self._set_motor(self.RIGHT_IN3, self.RIGHT_IN4, self.right_pwm, True, speed)

    def backward(self, speed: int):
        """Move backward at given speed (0-100) - both left and right motors"""
        self._set_motor(self.LEFT_IN1, self.LEFT_IN2, self.left_pwm, False, speed)
        self._set_motor(self.RIGHT_IN3, self.RIGHT_IN4, self.right_pwm, False, speed)

    def turn_left(self, speed: int):
        """Turn left - right motor forward, left motor backward"""
        self._set_motor(self.LEFT_IN1, self.LEFT_IN2, self.left_pwm, False, speed)
        self._set_motor(self.RIGHT_IN3, self.RIGHT_IN4, self.right_pwm, True, speed)

    def turn_right(self, speed: int):
        """Turn right - left motor forward, right motor backward"""
        self._set_motor(self.LEFT_IN1, self.LEFT_IN2, self.left_pwm, True, speed)
        self._set_motor(self.RIGHT_IN3, self.RIGHT_IN4, self.right_pwm, False, speed)

    def up(self, speed: int):
        """Move up at given speed (0-100) - both front and back motors"""
        self._set_motor(self.FRONT_IN1, self.FRONT_IN2, self.front_pwm, True, speed)
        self._set_motor(self.BACK_IN3, self.BACK_IN4, self.back_pwm, True, speed)

    def down(self, speed: int):
        """Move down at given speed (0-100) - both front and back motors"""
        self._set_motor(self.FRONT_IN1, self.FRONT_IN2, self.front_pwm, False, speed)
        self._set_motor(self.BACK_IN3, self.BACK_IN4, self.back_pwm, False, speed)

    def pitch_up(self, speed: int):
        """Pitch up - front motor down, back motor up"""
        self._set_motor(self.FRONT_IN1, self.FRONT_IN2, self.front_pwm, False, speed)
        self._set_motor(self.BACK_IN3, self.BACK_IN4, self.back_pwm, True, speed)

    def pitch_down(self, speed: int):
        """Pitch down - front motor up, back motor down"""
        self._set_motor(self.FRONT_IN1, self.FRONT_IN2, self.front_pwm, True, speed)
        self._set_motor(self.BACK_IN3, self.BACK_IN4, self.back_pwm, False, speed)

    def _set_motor(self, in1_pin: int, in2_pin: int, pwm_obj, forward: bool, speed: int):
        """Helper method to set individual motor direction and speed"""
        if forward:
            GPIO.output(in1_pin, GPIO.HIGH)
            GPIO.output(in2_pin, GPIO.LOW)
        else:
            GPIO.output(in1_pin, GPIO.LOW)
            GPIO.output(in2_pin, GPIO.HIGH)
        pwm_obj.ChangeDutyCycle(speed)

    def stop(self):
        """Stop all motors"""
        self.left_pwm.ChangeDutyCycle(0)
        self.right_pwm.ChangeDutyCycle(0)
        self.front_pwm.ChangeDutyCycle(0)
        self.back_pwm.ChangeDutyCycle(0)
        
        # Set all direction pins to LOW
        GPIO.output(self.LEFT_IN1, GPIO.LOW)
        GPIO.output(self.LEFT_IN2, GPIO.LOW)
        GPIO.output(self.RIGHT_IN3, GPIO.LOW)
        GPIO.output(self.RIGHT_IN4, GPIO.LOW)
        GPIO.output(self.FRONT_IN1, GPIO.LOW)
        GPIO.output(self.FRONT_IN2, GPIO.LOW)
        GPIO.output(self.BACK_IN3, GPIO.LOW)
        GPIO.output(self.BACK_IN4, GPIO.LOW)

    def cleanup(self):
        """Cleanup GPIO"""
        self.stop()
        GPIO.cleanup()
