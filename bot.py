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
import wiringpi2 as wiringpi


class RaspiRobotBoard:
    LEFT_GO_PIN = 10
    LEFT_DIR_PIN = 25
    RIGHT_GO_PIN = 17
    RIGHT_DIR_PIN = 4
    SW1_PIN = 11
    SW2_PIN = 9
    LED1_PIN = 7
    LED2_PIN = 8
    OC1_PIN = 22
    OC2_PIN = 21

    def __init__(self):
        GPIO.setmode(GPIO.BCM)

        GPIO.setup(self.LEFT_GO_PIN, GPIO.OUT)
        GPIO.setup(self.LEFT_DIR_PIN, GPIO.OUT)
        GPIO.setup(self.RIGHT_GO_PIN, GPIO.OUT)
        GPIO.setup(self.RIGHT_DIR_PIN, GPIO.OUT)

        GPIO.setup(self.LED1_PIN, GPIO.OUT)
        GPIO.setup(self.LED2_PIN, GPIO.OUT)
        GPIO.setup(self.OC1_PIN, GPIO.OUT)
        GPIO.setup(self.OC2_PIN, GPIO.OUT)

        GPIO.setup(self.SW1_PIN, GPIO.IN)
        GPIO.setup(self.SW2_PIN, GPIO.IN)

    def set_motors(self, left_go, left_dir, right_go, right_dir):
        GPIO.output(self.LEFT_GO_PIN, left_go)
        GPIO.output(self.LEFT_DIR_PIN, left_dir)
        GPIO.output(self.RIGHT_GO_PIN, right_go)
        GPIO.output(self.RIGHT_DIR_PIN, right_dir)

    def forward(self, seconds=0):
        self.set_motors(1, 0, 1, 0)
        if seconds > 0:
            time.sleep(seconds)
            self.stop()

    def stop(self):
        self.set_motors(0, 0, 0, 0)

    def reverse(self, seconds=0):
        self.set_motors(1, 1, 1, 1)
        if seconds > 0:
            time.sleep(seconds)
            self.stop()

    def left(self, seconds=0):
        self.set_motors(1, 0, 1, 1)
        if seconds > 0:
            time.sleep(seconds)
            self.stop()

    def right(self, seconds=0):
        self.set_motors(1, 1, 1, 0)
        if seconds > 0:
            time.sleep(seconds)
            self.stop()

    def sw1_closed(self):
        return not GPIO.input(self.SW1_PIN)

    def sw2_closed(self):
        return not GPIO.input(self.SW2_PIN)

    def set_led1(self, state):
        GPIO.output(self.LED1_PIN, state)

    def set_led2(self, state):
        GPIO.output(self.LED2_PIN, state)

    def set_oc1(self, state):
        GPIO.output(self.OC1_PIN, state)

    def set_oc2(self, state):
        GPIO.output(self.OC2_PIN, state)


def speach(text):
    # wiringpi2 breaks audio.
    f = codecs.open("/tmp/tts", "w", "utf-8")
    print(text)
    f.write(text)
    f.close()
    p = subprocess.Popen('/home/pi/aquestalkpi/AquesTalkPi -f /tmp/tts | aplay',
                         shell=True)
    

def get_ip_address_string():
    p = subprocess.Popen('hostname -I', shell=True, stdout=subprocess.PIPE)
    p.wait()
    return p.stdout.read()


class RaspiBot:
    GRIPPER_PIN_ID = 12
    CAMERA_PIN_ID = 13

    TRACKING_MARKER_ID = 6
    DANCE_MARKER_ID = 354
    WII_MARKER_ID = 1014

    def __init__(self, auto_start=False):
        GPIO.setwarnings(False)
        self._md = arucopy.MarkerDetector()
        self._rr = RaspiRobotBoard()
        wiringpi.wiringPiSetupGpio()
        self._auto_start = auto_start
        if auto_start:
            if not self._rr.sw1_closed():
                print('exit because switch is not closed')
            speach('開発モードで起動しました')
            speach('IPアドレスは%s' % get_ip_address_string())
            sys.exit()
        else:
            speach('こんにちは。よろしくね。')

        wiringpi.pinMode(self.GRIPPER_PIN_ID, wiringpi.GPIO.PWM_OUTPUT)
        wiringpi.pinMode(self.CAMERA_PIN_ID, wiringpi.GPIO.PWM_OUTPUT)
        wiringpi.pwmSetMode(wiringpi.GPIO.PWM_MODE_MS)
        wiringpi.pwmSetClock(400)
        wiringpi.pwmSetRange(1024)
        self.camera_front()
        self.gripper_open()
        self._rr.set_led1(False)
        self._rr.set_led2(False)

    def main(self):
        tracking_id = None
        while True:
            if self._auto_start and self._rr.sw2_closed():
                speach('おやすみするよ')
                self.camera_down()
                time.sleep(2)
                os.system('/sbin/poweroff')
            markers = self._md.detect()
            print('.', end='')
            sys.stdout.flush()
            if not markers:
                self._rr.set_led1(False)
                self._rr.set_led2(False)
                self._rr.stop()

            for marker in markers:
                print('[%d]: (%d, %d) area= %d' % (marker["id"],
                                                   marker["center_x"],
                                                   marker["center_y"],
                                                   marker["area"]))
                if marker["id"] == self.TRACKING_MARKER_ID:
                    if tracking_id != self.TRACKING_MARKER_ID:
                        speach('おいかけっこするよ')
                    self.track_marker(marker)
                elif marker["id"] == self.DANCE_MARKER_ID:
                    if tracking_id != self.DANCE_MARKER_ID:
                        speach('ダンスするね')
                    self.dance()
                elif marker["id"] == self.WII_MARKER_ID:
                    self.wii_control()
                elif marker["id"] == 724:
                    self._rr.set_led1(False)
                    self._rr.set_led2(True)
                    self._rr.forward()
                tracking_id = marker["id"]
            time.sleep(0.01)

    def track_marker(self, marker):
        if marker["area"] < 25000:
            if marker["center_x"] < 320 - 50:
                self._rr.set_motors(0, 1, 1, 1)
            elif marker["center_x"] > 320 + 50:
                self._rr.set_motors(1, 1, 0, 0)
            else:
                self._rr.forward()
        else:
            self._rr.reverse()

    def wii_control(self):
        import cwiid
        speach('ウィーコントローラーを準備してください')
        try:
            wm = cwiid.Wiimote()
        except RuntimeError:
            speach('ウィーコントローラーがみつからなかったよ')
            return
        speach('見つかりました')
        wm.led = 1
        for i in range(3):
            wm.rumble = True
            time.sleep(0.2)
            wm.rumble = False
            time.sleep(0.2)
        is_wii_control = True
        wm.rpt_mode = cwiid.RPT_BTN | cwiid.RPT_ACC
        while is_wii_control:
            if (wm.state['buttons'] & cwiid.BTN_UP):
                self._rr.forward()
            elif (wm.state['buttons'] & cwiid.BTN_LEFT):
                self._rr.left()
            elif (wm.state['buttons'] & cwiid.BTN_RIGHT):
                self._rr.right()
            elif (wm.state['buttons'] & cwiid.BTN_DOWN):
                self._rr.reverse()
            elif (wm.state['buttons'] & cwiid.BTN_PLUS):
                self.gripper_open()
            elif (wm.state['buttons'] & cwiid.BTN_MINUS):
                self.gripper_close()
            elif (wm.state['buttons'] & cwiid.BTN_1):
                self.camera_up()
            elif (wm.state['buttons'] & cwiid.BTN_2):
                self.camera_front()
            elif (wm.state['buttons'] & cwiid.BTN_HOME):
                self._rr.stop()
                is_wii_control = False
            else:
                self._rr.stop()
        speach('ウィーモードおしまい')

    def dance(self):
        self.camera_up()
        self.gripper_close()
        time.sleep(0.5)
        self.camera_down()
        self.gripper_open()
        time.sleep(0.5)
        self.camera_up()
        self.gripper_close()
        time.sleep(0.5)
        self.camera_down()
        self.gripper_open()
        time.sleep(0.5)
        self.camera_front()
        self._rr.reverse(1.5)
        self._rr.forward(1.5)
        self.camera_down()
        self.gripper_close()
        time.sleep(0.2)
        self.gripper_open()
        time.sleep(0.2)
        self.gripper_close()
        time.sleep(0.2)
        self.gripper_open()
        self.camera_front()
        self._rr.stop()

    def gripper_close(self, angle=70):
        wiringpi.pwmWrite(self.GRIPPER_PIN_ID, angle)

    def gripper_open(self, angle=50):
        wiringpi.pwmWrite(self.GRIPPER_PIN_ID, angle)

    def camera_down(self, angle=40):
        wiringpi.pwmWrite(self.CAMERA_PIN_ID, angle)

    def camera_up(self, angle=100):
        wiringpi.pwmWrite(self.CAMERA_PIN_ID, angle)

    def camera_front(self, angle=70):
        wiringpi.pwmWrite(self.CAMERA_PIN_ID, angle)

    def cleanup(self):
        wiringpi.pwmWrite(self.GRIPPER_PIN_ID, 0)
        wiringpi.pwmWrite(self.CAMERA_PIN_ID, 0)
        GPIO.cleanup()


if __name__ == '__main__':
    try:
        bot = RaspiBot(len(sys.argv) > 1)
        bot.main()
    except KeyboardInterrupt, e:
        pass
    bot.cleanup()
