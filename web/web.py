#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
#from __future__ import unicode_literals

import RPi.GPIO as GPIO
#import arucopy
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


import os
from geventwebsocket.handler import WebSocketHandler
from gevent import pywsgi

GPIO.setmode(GPIO.BCM)
mobile_base = DiffDriveMobileBase(
    PwmWithNotMotor(18, 17), PwmWithNotMotor(27, 22))

def vel_handle(environ, start_response):
    ws = environ['wsgi.websocket']
    speak(u'いらっしゃいませ').wait()
    while True:
        msg = ws.receive()
        if msg is None:
            break
        if msg == 'go_forward':
            mobile_base.set_velocity(-100) 
        elif msg == 'go_backward':
            mobile_base.set_velocity(100) 
        elif msg == 'go_left':
            mobile_base.set_velocity(0, -100)
        elif msg == 'go_right':
            mobile_base.set_velocity(0, 100)
        elif msg == 'go_stop':
            mobile_base.set_velocity(0) 
        elif msg == 'say_move':
            speak(u'どいてください')
        elif msg == 'say_hello':
            speak(u'こんにちは')
        # do something
    speak(u'また遊んでね').wait()


def myapp(environ, start_response):  
    path = environ["PATH_INFO"]
    print(path)
    if path == "/": 
        start_response("200 OK", [("Content-Type", "text/html")])  
        return open('./ui.html').read()
    elif path == "/ui.js": 
        start_response("200 OK", [("Content-Type", "text/html")])  
        return open('./ui.js').read()
    elif path == "/chibipibot":  
        return vel_handle(environ, start_response)
    elif path == "/image":  
        return image_handle(environ, start_response)


server = pywsgi.WSGIServer(('0.0.0.0', 8080), myapp, handler_class=WebSocketHandler)

server.serve_forever()
