#!/usr/bin/env python
# -*- coding: utf-8 -*-
import RPi.GPIO as GPIO
from time import sleep

class PwmMotor:
    def set_duty_cycle(self, signed_percent):
        pass
    def stop(self):
        pass


class PwmWithNotMotor(PwmMotor):
    def __init__(self, pin1, pin2, pwm_hz=50):
        GPIO.setup(pin1, GPIO.OUT)
        GPIO.setup(pin2, GPIO.OUT)
        self._pwm1 = GPIO.PWM(pin1, pwm_hz)
        self._pwm2 = GPIO.PWM(pin2, pwm_hz)
        self._pwm1.start(100)
        self._pwm2.start(100)
            
    def set_duty_cycle(self, signed_percent):
        if signed_percent > 100:
            signed_percent = 100
        if -signed_percent < -100:
            signed_percent = -100

        if signed_percent > 0:
            self._pwm1.ChangeDutyCycle(100 - signed_percent)
            self._pwm2.ChangeDutyCycle(100)
        elif signed_percent < 0:
            self._pwm1.ChangeDutyCycle(100)
            self._pwm2.ChangeDutyCycle(100 + signed_percent)
        else:
            self._pwm1.ChangeDutyCycle(100)
            self._pwm2.ChangeDutyCycle(100)
        
    def stop(self):
        self.set_duty_cycle(0)
        self._pwm1.stop()
        self._pwm2.stop()


class DiffDriveMobileBase(object):
    def __init__(self, pwm_motor_l, pwm_motor_r):
        self._motor_l = pwm_motor_l
        self._motor_r = pwm_motor_r

    def set_velocity(self, vel_x, vel_theta=0):
        self._motor_l.set_duty_cycle(vel_x - vel_theta)
        self._motor_r.set_duty_cycle(vel_x + vel_theta)

    def stop(self):
        self._motor_l.stop()
        self._motor_r.stop()

class TouchSensor(object):
    def __init__(self, pin):
        GPIO.setup(pin, GPIO.IN)
        self._pin = pin

    def is_touched(self):
        return GPIO.input(self._pin)


if __name__ == '__main__':
    GPIO.setmode(GPIO.BCM)
    sensor1 = TouchSensor(9)
    sensor2 = TouchSensor(10)
    mobile_base = DiffDriveMobileBase(PwmWithNotMotor(18, 17), PwmWithNotMotor(27, 22))
    mobile_base.set_velocity(50, 0)
    sleep(1)
    mobile_base.set_velocity(0, 100)
    sleep(1)
    mobile_base.set_velocity(0, -100)
    sleep(1)
    mobile_base.set_velocity(-50, 0)
    sleep(1)
    mobile_base.set_velocity(100, 0)
    sleep(1)
    mobile_base.set_velocity(0, 0)
    sleep(1)
    mobile_base.stop()
    GPIO.cleanup()
