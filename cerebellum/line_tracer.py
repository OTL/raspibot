#!/usr/bin/env python
# -*- coding: utf-8 -*-

from chibipibot_driver import PwmRGB
from chibipibot_driver import ChibiPiBot
import time

def test_trace():
    c = ChibiPiBot()
    led = PwmRGB(6, 12, 5)
    try:
        while True:
            s = c.get_sensor_data()
            print s
            if s['touch_r'] == 1 or s['touch_l'] == 1:
                c.set_velocity(-100)
                time.sleep(0.5)
            elif s['photo_r'] > 2000 and s['photo_l'] > 2000:
                print 'in air'
                c.set_velocity(80)
                led.set_rgb(100, 0, 0)
            elif s['photo_r'] > 2000:
                c.set_velocity(0, 100)
                print 'r'
                led.set_rgb(100, 100, 0)
            elif s['photo_l'] > 2000:
                c.set_velocity(0, -100)
                print 'l'
                led.set_rgb(0, 0, 100)
            else:
                c.set_velocity(100)
                print 'f'
                led.set_rgb(0, 100, 0)
            time.sleep(0.1)
    except KeyboardInterrupt:
        c.set_velocity(0)
        led.set_rgb(0, 0, 0)


if __name__ == '__main__':
    test_trace()
