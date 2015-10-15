#!/usr/bin/env python
# -*- coding: utf-8 -*-

import RPi.GPIO as GPIO
import threading
import time
from collections import deque

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


class SpiDriver(object):

    def __init__(self, clk_pin=11, mosi_pin=10, miso_pin=9, ss_pin=8):
        self._clk = clk_pin
        self._mosi = mosi_pin
        self._miso = miso_pin
        self._ss = ss_pin
        GPIO.setup(mosi_pin, GPIO.OUT)
        GPIO.setup(miso_pin, GPIO.IN)
        GPIO.setup(clk_pin, GPIO.OUT)
        GPIO.setup(ss_pin, GPIO.OUT)

    def read(self, ch):
        GPIO.output(self._ss,   False)
        GPIO.output(self._clk,  False)
        GPIO.output(self._mosi, False)
        GPIO.output(self._clk,  True)
        GPIO.output(self._clk,  False)

        # 測定するチャンネルの指定をADコンバータに送信
        cmd = (ch | 0x18) << 3
        for i in range(5):
            if (cmd & 0x80):
                GPIO.output(self._mosi, True)
            else:
                GPIO.output(self._mosi, False)
            cmd <<= 1
            GPIO.output(self._clk, True)
            GPIO.output(self._clk, False)
        GPIO.output(self._clk, True)
        GPIO.output(self._clk, False)
        GPIO.output(self._clk, True)
        GPIO.output(self._clk, False)

        # 12ビットの測定結果をADコンバータから受信
        value = 0
        for i in range(12):
            value <<= 1
            GPIO.output(self._clk, True)
            if (GPIO.input(self._miso)):
                value |= 0x1
            GPIO.output(self._clk, False)
        GPIO.output(self._ss, True)
        return value


#import numpy as np

class AverageData(object):
    def __init__(self, size):
        self._queue = deque(maxlen=size)

    def push(self, data):
        self._queue.append(data)

    def get_average(self):
        return sum(self._queue) / float(len(self._queue))


class ChibiPiBot(object):

    def __init__(self):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        self._touch_sensor_l = TouchSensor(19)
        self._touch_sensor_r = TouchSensor(20)
        self._photo_sensor_l = TouchSensor(5)
        self._photo_sensor_r = TouchSensor(6)
        self._mic_sensor_r = TouchSensor(13)
        self._spi = SpiDriver()
        self._mic_r_queue = AverageData(5)
        self._mic_l_queue = AverageData(5)
        self._mobile_base = DiffDriveMobileBase(
            PwmWithNotMotor(17, 18), PwmWithNotMotor(22, 27))
        self._thread = threading.Thread(target=self._check_timeout)
        self._thread.setDaemon(True)
        self._thread.start()
        self._lock = threading.Lock()
        self._last_updated_time = time.mktime(time.localtime())

    def _check_timeout(self):
        while True:
            time.sleep(0.1)
            if time.mktime(time.localtime()) - self._last_updated_time > 1.0:
                with self._lock:
                    self._mobile_base.set_velocity(0, 0)

    def set_velocity(self, vel_x, vel_theta=0):
        with self._lock:
            self._mobile_base.set_velocity(vel_x, vel_theta)
        self._last_updated_time = time.mktime(time.localtime())

    def get_sensor_data(self):
        '''returns the dictionary which contains sensor data'''
        self._mic_l_queue.push(abs(2048 - self._spi.read(1)))
        self._mic_r_queue.push(abs(2048 - self._spi.read(0)))
        return {'touch_l': self._touch_sensor_l.is_touched(),
                'touch_r': self._touch_sensor_r.is_touched(),
                'photo_l': self._photo_sensor_l.is_touched(),
                'photo_r': self._photo_sensor_r.is_touched(),
                'mic_r': self._mic_r_queue.get_average(),
                'mic_l': self._mic_l_queue.get_average(),
                'temperature': self._spi.read(2) * 3.3 / 4096 * 100,
                }


if __name__ == '__main__':
    c = ChibiPiBot()
    while True:
        print c.get_sensor_data()
#        if c.get_sensor_data()['photo_l']:
#            c.set_velocity(-100)
#        else:
#            c.set_velocity(0)
        time.sleep(0.1)

