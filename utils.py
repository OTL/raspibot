#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import unicode_literals

import codecs
import os
import subprocess

def speach(text):
    f = codecs.open("/tmp/tts", "w", "utf-8")
    print(text)
    f.write(text)
    f.close()
    p = subprocess.Popen('/home/pi/aquestalkpi/AquesTalkPi -f /tmp/tts | aplay',
                         shell=True)
    return p
    

def get_ip_address_string():
    p = subprocess.Popen('hostname -I', shell=True, stdout=subprocess.PIPE)
    p.wait()
    return p.stdout.read()

import urllib2
import json

def get_weather():
    weather_data = urllib2.urlopen('http://api.openweathermap.org/data/2.5/weather?q=Tokyo,jp')
    json_weather = json.load(weather_data)
    max_temp = json_weather['main']['temp_max'] - 273.15
    min_temp = json_weather['main']['temp_min'] - 273.15
    #weather_desc = json_weather['weather'][0]['description']
    return (max_temp, min_temp)

#speach('IPアドレスは%s' % get_ip_address_string()).wait()
#speach('最高気温は%d度 最低気温は%d度です' % get_weather()).wait()
