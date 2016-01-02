#!/usr/bin/env python
# -*- coding: utf-8 -*-

from chibipibot_driver import PwmRGB
from chibipibot_driver import ChibiPiBot
import time
from mpu_6050 import Mpu6050Reader
from utils import speak

def test_choro_q():
    c = ChibiPiBot(timeout_sec=5.0)
    led = PwmRGB(6, 12, 5)
    imu = Mpu6050Reader()
    imu_data_offset = imu.get_acceleration()[1]
    try:
        while True:
            s = c.get_sensor_data()
            print s
            if s['photo_r'] < 2000 and s['photo_l'] < 2000:
                print 'on ground'
                print imu.get_angular_velocity()
                imu_data = imu.get_acceleration()[1] - imu_data_offset
                imu_rot = imu.get_angular_velocity()[2]
                print imu_data
                if imu_data > 1 and imu_data < 5:
                    if imu_data > 3:
                        speak(u'どーん')
                    else:
                        speak(u'ぶいーん')
                    c.set_velocity(100)
                    led.set_rgb(0, 0, 100)
                    print '1'
                    time.sleep(min(5.0, imu_data))
                    print '2'
                    c.set_velocity(0)
                    led.set_rgb(0, 0, 0)
                    print '3'
                    time.sleep(0.5)
                    print '4'
                elif abs(imu_rot) > 1.0 and abs(imu_rot) < 5.0:
                    speak(u'くるくるー')
                    if imu_rot > 0.0:
                        c.set_velocity(0, 100)
                        led.set_rgb(100, 0, 0)
                    else:
                        c.set_velocity(0, -100)
                        led.set_rgb(0, 100, 0)
                    time.sleep(min(5.0, abs(imu_rot)))
                    c.set_velocity(0)
                    led.set_rgb(0, 0, 0)
            time.sleep(0.1)
    except KeyboardInterrupt:
        c.set_velocity(0)
        led.set_rgb(0, 0, 0)


if __name__ == '__main__':
    test_choro_q()
