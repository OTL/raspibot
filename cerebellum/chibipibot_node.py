#!/usr/bin/env python

import jps
import json
import time
from chibipibot_driver import ChibiPiBot
from chibipibot_driver import PwmRGB

class ChibiPiBotNode(object):
    
    def __init__(self, host='localhost'):
        self._c = ChibiPiBot()
        self._led1 = PwmRGB(16, 19, 26)
        self._led2 = PwmRGB(12, 6, 13)
        self._pub = jps.Publisher('sensor', host=host)
        self._sub_vel = jps.Subscriber('cmd_vel', self._vel_callback, host=host)
        self._sub_led1 = jps.Subscriber('led1', self._led1_callback, host=host)
        self._sub_led2 = jps.Subscriber('led2', self._led2_callback, host=host)

    def _vel_callback(self, msg):
        try:
            vel = json.loads(msg)
            self._c.set_velocity(vel["x"], vel["theta"])
        except ValueError as e:
            print msg
            print e

    def _led1_callback(self, msg):
        try:
            led = json.loads(msg)
            self._led1.set_rgb(led.get("r"), led.get("g"), led.get("b"))
        except ValueError as e:
            print msg
            print e

    def _led2_callback(self, msg):
        try:
            led = json.loads(msg)
            self._led2.set_rgb(led.get("r"), led.get("g"), led.get("b"))
        except ValueError as e:
            print msg
            print e
            
    def main(self):
        while True:
            s = self._c.get_sensor_data()
            self._pub.publish(json.dumps(s))
            self._sub_vel.spin_once()
            self._sub_led1.spin_once()
            self._sub_led2.spin_once()
            time.sleep(0.1)


def main():
    node = ChibiPiBotNode('smilerobotics.com')
    node.main()

if __name__ == '__main__':
    main()
