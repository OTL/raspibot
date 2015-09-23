#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import unicode_literals

import RPi.GPIO as GPIO
import arucopy
import codecs
import os
import subprocess
import sys
import time

from chibi import DiffDriveMobileBase
from chibi import PwmWithNotMotor
from utils import speak
from utils import get_ip_address_string
from utils import get_weather_temperature

class RaspiBot:
    TRACKING_MARKER_ID = 119
    DANCE_MARKER_ID = 110
    TAPE_MARKER_ID = 106
    WII_MARKER_ID = 103
    TESTER_MARKER_ID = 116

    def __init__(self):
        self._mobile_base = DiffDriveMobileBase(
            PwmWithNotMotor(18, 17), PwmWithNotMotor(27, 22))
        speak('おはようございます').wait()
        speak('IPアドレスは%sです' % get_ip_address_string()).wait()
        speak('最高気温は%d度 最低気温は%d度です' %
              get_weather_temperature()).wait()
        self._md = arucopy.MarkerDetector()

    def main(self):
        tracking_id = None
        while True:
            markers = self._md.detect()
            print('.', end='')
            sys.stdout.flush()
            if not markers:
                self._mobile_base.set_velocity(0)

            for marker in markers:
                print('[%d]: (%d, %d) area= %d' % (marker["id"],
                                                   marker["center_x"],
                                                   marker["center_y"],
                                                   marker["area"]))
                if marker["id"] == self.TRACKING_MARKER_ID:
                    if tracking_id != self.TRACKING_MARKER_ID:
                        speak('ケータイを見つけたよ').wait()
                        speak('追いかけるよ')
                    self.track_marker(marker)
                elif marker["id"] == self.DANCE_MARKER_ID:
                    if tracking_id != self.DANCE_MARKER_ID:
                        speak('ダンスするね')
                    self.dance()
                else:
                    speak('%d番は登録されていません' % marker["id"]).wait()
                tracking_id = marker["id"]
            time.sleep(0.01)

    def track_marker(self, marker):
        if marker["area"] < 5000:
            if marker["center_x"] < 320 - 50:
                self._rr.set_motors_pwm(0, 1)
            elif marker["center_x"] > 320 + 50:
                self._rr.set_motors_pwm(1, 0)
            else:
                self._rr.forward()
        else:
            self._rr.reverse()

    def dance(self):
        pass

    def cleanup(self):
        GPIO.cleanup()


if __name__ == '__main__':
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        bot = RaspiBot()
        bot.main()
    except KeyboardInterrupt, e:
        pass
    bot.cleanup()
