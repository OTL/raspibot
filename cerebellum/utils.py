#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import unicode_literals

import codecs
import collections
import os
import subprocess
import re


class AverageFilter(object):
    def __init__(self, length):
        self._buffer = collections.deque([], length)

    def append(self, data):
        self._buffer.append(data)

    def get_average(self):
        l = list(self._buffer)
        s = 0.0
        for d in l:
            s += d
        return s / float(len(l))


def set_wifi_from_string(text):
    '''text is 'ssid:hgoehoge\npasswd:hogehoge' '''
    m = re.match('^ssid:\s*(.+)\s*^passwd:\s*(.+)\s*', text, re.MULTILINE)
    if m is not None:
        ssid = m.group(1)
        speak(u'%sに接続します' % ssid)
        passwd = m.group(2)
        devnull = open(os.devnull, 'wb')
        p1 = subprocess.Popen('/usr/bin/wpa_passphrase %s %s |grep -v \#|grep psk= |sed -e s/"\s"psk=//' % (ssid, passwd), stdout=subprocess.PIPE, shell=True)
        p1.wait()
        encoded_passwd = p1.stdout.read().replace('\n', '')
        print(encoded_passwd)
        tmp_file_path = '/tmp/wpa_supplicant.conf'
        subprocess.Popen('/bin/cat /etc/wpa_supplicant/wpa_supplicant.conf |sed -e s/psk=.*/psk=%s/ | sed -e s/ssid=".*"/ssid=\\"%s\\"/ > %s' % (encoded_passwd, ssid, tmp_file_path),
                         stdout=devnull,
                         stderr=devnull,
                         shell=True).wait()
        subprocess.Popen('/bin/cp -b %s /etc/wpa_supplicant/wpa_supplicant.conf' % tmp_file_path, shell=True).wait()
        subprocess.Popen('/etc/init.d/networking restart', shell=True).wait()
        devnull.close()
        print ('%s %s' % (ssid, passwd))
        speak('IPアドレスは%s' % get_ip_address_string()).wait()


def speak(text):
    AQUESTALK_PATH = '/home/pi/aquestalkpi/AquesTalkPi'
    TEMP_TEXT_PATH = '/tmp/tts'
    f = codecs.open(TEMP_TEXT_PATH, 'w', 'utf-8')
    print(text)
    f.write(text)
    f.close()
    devnull = open(os.devnull, 'wb')
    p = subprocess.Popen('%s -f %s | aplay' % (AQUESTALK_PATH, TEMP_TEXT_PATH),
                         stdout=devnull,
                         stderr=devnull,
                         shell=True)
    devnull.close()
    return p

import sys

def play_sound(file_path):
    this_dir = os.path.dirname(sys.argv[0])
    devnull = open(os.devnull, 'wb')
    p = subprocess.Popen('aplay %s/wav/%s' % (this_dir, file_path),
                         stdout=devnull, stderr=devnull, shell=True)
    devnull.close()
    return p


def get_ip_address_string():
    p = subprocess.Popen('hostname -I', shell=True, stdout=subprocess.PIPE)
    p.wait()
    return p.stdout.read()


import urllib2
import json


def get_weather_temperature():
    weather_data = urllib2.urlopen(
        'http://api.openweathermap.org/data/2.5/weather?q=Tokyo,jp')
    json_weather = json.load(weather_data)
    max_temp = json_weather['main']['temp_max'] - 273.15
    min_temp = json_weather['main']['temp_min'] - 273.15
    #weather_desc = json_weather['weather'][0]['description']
    return (max_temp, min_temp)

if __name__ == '__main__':
#    speak('こんにちわ').wait()
#    speak('IPアドレスは%s' % get_ip_address_string()).wait()
    set_wifi_from_string('ssid:otl001\npasswd:qwertyuiop')
