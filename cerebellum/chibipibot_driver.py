#!/usr/bin/env python
# -*- coding: utf-8 -*-

import RPi.GPIO as GPIO
import threading
import time
from utils import AverageFilter
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


class BinaryNotMotor(PwmMotor):

    def __init__(self, pin1, pin2):
        GPIO.setup(pin1, GPIO.OUT)
        GPIO.setup(pin2, GPIO.OUT)
        self._pin1 = pin1
        self._pin2 = pin2

    def set_duty_cycle(self, signed_percent):
        if signed_percent > 100:
            signed_percent = 100
        if -signed_percent < -100:
            signed_percent = -100

        if signed_percent > 0:
            GPIO.output(self._pin1, False)
            GPIO.output(self._pin2, True)
        elif signed_percent < 0:
            GPIO.output(self._pin1, True)
            GPIO.output(self._pin2, False)
        else:
            GPIO.output(self._pin1, False)
            GPIO.output(self._pin2, False)

    def stop(self):
        GPIO.output(self._pin1, False)
        GPIO.output(self._pin2, False)


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

    def __init__(self, timeout_sec=1.0):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        self._touch_sensor_l = TouchSensor(21)
        self._touch_sensor_r = TouchSensor(20)
        self._spi = SpiDriver()
        self._mic_r_queue = AverageData(5)
        self._mic_l_queue = AverageData(5)
        self._mobile_base = DiffDriveMobileBase(
            PwmWithNotMotor(17, 18), PwmWithNotMotor(22, 27))
        self._is_stopping = False
        self._thread = threading.Thread(target=self._check_timeout)
        self._thread.setDaemon(True)
        self._thread.start()
        self._lock = threading.Lock()
        self._last_updated_time = time.mktime(time.localtime())
        self._timeout_sec = timeout_sec
        self._a_charge_filter = AverageFilter(20)

    def stop(self):
        self._is_stopping = True
        self.set_velocity(0)

    def _check_timeout(self):
        while not self._is_stopping:
            time.sleep(0.1)
            if time.mktime(time.localtime()) - self._last_updated_time > self._timeout_sec:
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
        photo_l = self._spi.read(6)
        photo_r = self._spi.read(5)
        photo_rl = self._spi.read(2)
        photo_rr = self._spi.read(3)
#        a_charge_raw_val = self._spi.read(7)
        # -300 is magic number.
#        a_charge_raw_v = a_charge_raw_val * 3.3 / 4096.0
#        a_charge_raw_v = (a_charge_raw_val - 3000) * 3.3 / 4096.0
#        self._a_charge_filter.append((a_charge_raw_v - 2.5) / 0.185)
        return {'touch_l': self._touch_sensor_l.is_touched(),
                'touch_r': self._touch_sensor_r.is_touched(),
                'photo_l': photo_l,
                'photo_r': photo_r,
                'photo_rl': photo_rl,
                'photo_rr': photo_rr,
                'mic_r': self._mic_r_queue.get_average(),
                'mic_l': self._mic_l_queue.get_average(),
                'v_batt': round(self._spi.read(4) * 2.0 * 3.3 / 4096.0, 2),
                'v_charge': round(self._spi.read(7) * 2.0 * 3.3 / 4096.0, 2),
                }

import colorsys

class PwmRGB(object):
    def __init__(self, pin_r, pin_g, pin_b, pwm_hz=50):
        GPIO.setup(pin_r, GPIO.OUT)
        GPIO.setup(pin_g, GPIO.OUT)
        GPIO.setup(pin_b, GPIO.OUT)
        self._pwm_r = GPIO.PWM(pin_r, pwm_hz)
        self._pwm_g = GPIO.PWM(pin_g, pwm_hz)
        self._pwm_b = GPIO.PWM(pin_b, pwm_hz)
        for pwm in [self._pwm_r, self._pwm_g, self._pwm_b]:
            pwm.start(0)

    def set_rgb(self, percent_r, percent_g, percent_b):
        self._pwm_r.ChangeDutyCycle(percent_r)
        self._pwm_g.ChangeDutyCycle(percent_g)
        self._pwm_b.ChangeDutyCycle(percent_b)

    def set_hsv(self, percent_h,  percent_s,  percent_v):
        r, g, b = colorsys.hsv_to_rgb(percent_h * 0.01, percent_s * 0.01, percent_v * 0.01)
        self.set_rgb(r * 100, g * 100, b * 100)


def test_led():
    GPIO.setmode(GPIO.BCM)
    led1 = PwmRGB(19, 26, 16)
    led2 = PwmRGB(6, 13, 12)
    i = 0
    import math
    while True:
        led1.set_hsv(i % 100, 80, int(math.sin(math.radians(i * 10)) * 50 + 50))
        led2.set_hsv(i % 100, 80, int(math.sin(math.radians(i * 10)) * 50 + 50))
        i = i + 1
        time.sleep(0.1)

def test_sensor():
    c = ChibiPiBot()
    while True:
        s = c.get_sensor_data()
        print s
        time.sleep(0.1)

def test_motor():
    c = ChibiPiBot()
    c.set_velocity(100, 0)
    time.sleep(0.5)
    c.set_velocity(-100, 0)
    time.sleep(0.5)
    c.set_velocity(0, 100)
    time.sleep(0.5)
    c.set_velocity(0, -100)
    time.sleep(0.5)
    c.set_velocity(0, 0)
    time.sleep(0.5)

if __name__ == '__main__':
    test_led()
#    test_sensor()
#    test_motor()

#        print s
#        c.set_velocity(100, 0)
#        time.sleep(1)
#        c.set_velocity(-100, 0)
#        time.sleep(1)
#        c.set_velocity(0, 0)
#        time.sleep(1)
#        with open('v_charge.txt', 'a') as f:
#            f.write('%d %f\n' % (i, s['v_charge']))
#        time.sleep(1)
#        print s['v_charge']
#        i += 1
