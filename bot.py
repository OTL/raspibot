#!/usr/bin/env python
import sys
import RPi.GPIO as GPIO
from raspirobotboard import *
import arucopy
import time

GPIO.setwarnings(False)
md = arucopy.MarkerDetector()
rr = RaspiRobot()

auto_start = len(sys.argv) > 1
if auto_start and not rr.sw1_closed():
    print 'exit because switch is not closed'
    sys.exit()

rr.set_led1(False)
rr.set_led2(False)

def track_marker(marker):
    if marker["area"] < 25000:
        if marker["center_x"] < 320 - 50:
            rr.set_motors(0, 0, 1, 1)
        elif marker["center_x"] > 320 + 50:
            rr.set_motors(1, 1, 0, 1)
        else:
            rr.reverse()
    else:
        rr.forward()

def dance():
    rr.forward(1.5)
    rr.reverse(1.5)
    rr.left(1.5)
    rr.right(1.5)
    rr.left(1.5)
    rr.right(5)
    rr.stop()
    
while True:
    if auto_start and rr.sw2_closed():
        import os
        print 'shutdown by switch2'
        os.system('/sbin/poweroff')
        
    markers = md.detect()
    if not markers:
        rr.set_led1(False)
        rr.set_led2(False)
        rr.stop()

    for marker in markers:
        print '[%d]: (%d, %d) %d'%(marker["id"],
                                   marker["center_x"],
                                   marker["center_y"],
                                   marker["area"])
        if marker["id"] == 6:
            track_marker(marker)
        elif marker["id"] == 354:
            dance()
        elif marker["id"] == 1014:
            rr.set_led1(True)
            rr.set_led2(False)
            rr.forward()
        elif marker["id"] == 724:
            rr.set_led1(False)
            rr.set_led2(True)
            rr.reverse()

    time.sleep(0.01)

