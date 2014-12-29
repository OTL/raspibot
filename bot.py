#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import subprocess
import codecs
import sys
import RPi.GPIO as GPIO
from raspirobotboard import *
import arucopy
import time
import wiringpi2 as wiringpi


def speach(text):
    # wiringpi2 breaks audio.
    f = codecs.open("/tmp/tts", "w", "utf-8")
    f.write(text)
    f.close()
    os.system("/home/pi/aquestalkpi/AquesTalkPi -f /tmp/tts | aplay")

def track_marker(marker):
    if marker["area"] < 25000:
        if marker["center_x"] < 320 - 50:
            rr.set_motors(1, 1, 0, 1)
        elif marker["center_x"] > 320 + 50:
            rr.set_motors(0, 0, 1, 1)
        else:
            rr.reverse()
    else:
        rr.forward()

def dance():
    camera_up()
    gripper_close()
    time.sleep(0.5)
    camera_down()
    gripper_open()
    time.sleep(0.5)
    camera_up()
    gripper_close()
    time.sleep(0.5)
    camera_down()
    gripper_open()
    time.sleep(0.5)
    camera_front()
    rr.forward(1.5)
    rr.reverse(1.5)
    camera_down()
    gripper_close()
    time.sleep(0.2)
    gripper_open()
    time.sleep(0.2)
    gripper_close()
    time.sleep(0.2)
    gripper_open()
    camera_front()
    rr.stop()


def gripper_close():
    wiringpi.pwmWrite(GRIPPER_PIN_ID, 70)

def gripper_open():
    wiringpi.pwmWrite(GRIPPER_PIN_ID, 50)

def camera_down(angle=40):
    wiringpi.pwmWrite(CAMERA_PIN_ID, angle)

def camera_up(angle=100):
    wiringpi.pwmWrite(CAMERA_PIN_ID, angle)

def camera_front(angle=70):
    wiringpi.pwmWrite(CAMERA_PIN_ID, angle)

    
GPIO.setwarnings(False)
md = arucopy.MarkerDetector()
rr = RaspiRobot()
wiringpi.wiringPiSetupGpio()

GRIPPER_PIN_ID = 12
CAMERA_PIN_ID = 13

auto_start = len(sys.argv) > 1
if auto_start:
    if not rr.sw1_closed():
        print 'exit because switch is not closed'
        speach(u'開発モードで起動しました')
        p = subprocess.Popen('hostname -I', shell=True, stdout=subprocess.PIPE)
        p.wait()
        ip_address = p.stdout.read()
        speach(u'IPアドレスは%s' % ip_address)
        sys.exit()
    else:
        speach(u'こんにちは。よろしくね。')

def init():
    wiringpi.pinMode(GRIPPER_PIN_ID, wiringpi.GPIO.PWM_OUTPUT)
    wiringpi.pinMode(CAMERA_PIN_ID, wiringpi.GPIO.PWM_OUTPUT)
    wiringpi.pwmSetMode(wiringpi.GPIO.PWM_MODE_MS)
    wiringpi.pwmSetClock(400)
    wiringpi.pwmSetRange(1024)
    camera_front()
    gripper_open()
    rr.set_led1(False)
    rr.set_led2(False)

def main():
    while True:
        if auto_start and rr.sw2_closed():
            print 'shutdown by switch2'
            speach(u'おやすみするよ')
            camera_down()
            time.sleep(2)
            os.system('/sbin/poweroff')
        tracking_id = None
        markers = md.detect()
        print '.'
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
                if tracking_id != 6:
                    speach(u'おいかけっこするよ')
                track_marker(marker)
            elif marker["id"] == 354:
                if tracking_id != 354:
                    speach(u'ダンスするね')
                dance()
            elif marker["id"] == 1014:
                rr.set_led1(True)
                rr.set_led2(False)
                rr.forward()
            elif marker["id"] == 724:
                rr.set_led1(False)
                rr.set_led2(True)
                rr.reverse()
            tracking_id = marker["id"]
        time.sleep(0.01)


if __name__ == '__main__':
    try:
        init()
        main()
    except KeyboardInterrupt, e:
        GPIO.cleanup()
