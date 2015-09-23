#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import RPi.GPIO as GPIO
import subprocess
import sys
import time
import socket

from chibi import DiffDriveMobileBase
from chibi import TouchSensor
from chibi import PwmWithNotMotor
from utils import speak
from utils import get_ip_address_string
from utils import get_weather_temperature

GPIO.setmode(GPIO.BCM)
mobile_base = DiffDriveMobileBase(PwmWithNotMotor(17, 18), PwmWithNotMotor(22, 27))
    
sensor_l = TouchSensor(9)
sensor_r = TouchSensor(10)

sensor = {}

import xmlrpclib

s = xmlrpclib.ServerProxy('http://smilerobotics.com:12346')
while True:
    time.sleep(0.5)
    sensor['touch_l'] = sensor_l.is_touched()
    sensor['touch_r'] = sensor_r.is_touched()
    try:
        socket.setdefaulttimeout(1)
        command = s.get_command(sensor)
        socket.setdefaulttimeout(None)
        if command['velocity']:
            mobile_base.set_velocity(*command['velocity'])
        if command['speak']:
            speak(command['speak'])
    except socket.error as e:
        print(e)
        mobile_base.set_velocity(0, 0)
