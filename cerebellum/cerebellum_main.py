#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys, codecs
sys.stdout = codecs.lookup('utf_8')[-1](sys.stdout)

import collections
import os
import random
import threading
import time

from rpc_client import CerebrumRpcClient
from sensors import SensorDataCollector
from sensors import Emotion
from chibipibot_driver import ChibiPiBot
import utils
import vision

def touch_motion(sensor_dict, command, history, ignoring_time):
    if sensor_dict['touch_l'] and sensor_dict['touch_r']:
        command['speak'] = u'おさないでー'
        command['velocity'] = (-100, 0)
        command['emotion'] = -1000
    elif sensor_dict['touch_l']:
        command['dance'] = 3
#            command['speak'] = u'左へ曲がるよ'
        command['sound'] = 'move'
        command['emotion'] = 500
    elif sensor_dict['touch_r']:
        command['dance'] = 4
        command['sound'] = 'move'
        command['emotion'] = 500

def emotional_motion(sensor_dict, command, history, ignoring_time):
    if sensor_dict['emotion'] > 3000:
        command['speak'] = u'楽しくなってきた！'
        command['emotion'] = -2000
        command['dance'] = 1

def show_network(sensor_dict, command, history, ignoring_time):
    if sensor_dict['is_online'] and not history[-1]['is_online']:
        command['speak'] = u'ネットワークに接続したよ'
    if not sensor_dict['is_online'] and history[-1]['is_online']:
        command['speak'] = u'ネットワークから切断したみたい'

def connect_network_by_code(sensor_dict, command, history, ignoring_time):
    if not sensor_dict['is_online'] and sensor_dict.get('code'):
        utils.set_wifi_from_string(sensor_dict['code'])

def speak_time(sensor_dict, command, history, ignoring_time):
    if sensor_dict['oclock_hour'] is not None and (
        history[-1]['oclock_hour'] is None):
        command['speak'] = u'%d時ちょうどになったね' % sensor_dict['oclock_hour']
        command['sound'] = 'oclock'
        command['dance'] = 1
    def check_hour(i):
        if sensor_dict['from_start_sec'] >= i * 60 * 60 and (
            history[-1]['from_start_sec'] < i * 60 * 60):
            return i
        return None
    for i in range(5):
        hour = check_hour(i)
        if hour:
            command['speak'] = u'動き出して%d時間たったよ' % hour
            command['dance'] = 1


def shutdown_by_vision(sensor_dict, command, history, ignoring_time):
    if sensor_dict['darkness'] and sensor_dict['touch_l'] and sensor_dict['touch_r']:
        command['speak'] = u'電源を切ります'
        command['system'] = 'poweroff'

def deal_emotion(sensor_dict, command, history, ignoring_time):
    if not command:
        command['emotion'] = -10

def listen_sound(sensor_dict, command, history, ignoring_time):
    if 'mic' in ignoring_time and (ignoring_time['mic'] < sensor_dict['from_start_sec']):
        if sensor_dict.get('mic_r') and sensor_dict.get('mic_l'):
            if sensor_dict.get('mic_r') > 30 and sensor_dict.get('mic_l') > 30:
                command['velocity'] = (80, 0)
                command['speak'] = u'はいはい'
                ignoring_time['mic'] = sensor_dict['from_start_sec'] + 2
            elif sensor_dict.get('mic_r') > 10 and sensor_dict.get('mic_l') > 10:
                if sensor_dict.get('mic_r') - 10 > sensor_dict.get('mic_l'):
                    command['velocity'] = (0, 80)
                    ignoring_time['mic'] = sensor_dict['from_start_sec'] + 2
                elif sensor_dict.get('mic_r') < sensor_dict.get('mic_l') - 10:
                    command['velocity'] = (0, -80)
                    ignoring_time['mic'] = sensor_dict['from_start_sec'] + 2

def check_ground(sensor_dict, command, history, ignoring_time):
    if 'photo_r' in sensor_dict and 'photo_l' in sensor_dict:
        if sensor_dict['photo_l'] == 1 and sensor_dict['photo_r'] == 1:
            rand = random.random()
            if rand < 0.5:
                command['dance'] = 5
            else:
                command['dance'] = 6
            command['sound'] = 'back'
        elif sensor_dict['photo_l'] == 1:
            command['dance'] = 5
            command['sound'] = 'back'
        elif sensor_dict['photo_l'] == 1:
            command['dance'] = 6
            command['sound'] = 'back'

def random_motion(sensor_dict, command, history, ignoring_time):
    if 'velocity' not in command:
        rand = random.random()
        if sensor_dict['emotion'] < -2000:
            if rand < 0.1:
                command['velocity'] = (80, 0)
            elif rand < 0.25:
                command['velocity'] = (0, 80)
            elif rand < 0.4:
                command['velocity'] = (0, -80)
        else:
            if rand < 0.05:
                command['velocity'] = (80, 0)
            elif rand < 0.15:
                command['velocity'] = (0, 80)
            elif rand < 0.25:
                command['velocity'] = (0, -80)

def overwrite_direct_command(sensor_dict, command, history, ignoring_time):
    if sensor_dict['command_velocity']:
        command['velocity'] = sensor_dict['command_velocity']
    if sensor_dict['command_speak']:
        command['speak'] = sensor_dict['command_speak']


class Cerebellum(object):

    def __init__(self):
        self._emotion = Emotion()
        self._robot_driver = ChibiPiBot()
        self._sensor = SensorDataCollector(robot_driver=self._robot_driver,
                                           emotion=self._emotion,
                                           cerebrum_getter=CerebrumRpcClient())
        self._sensor_history = collections.deque([self._sensor.get_sensor_data()], 100)
        self._vision = vision.VisionSensor()
        self._command = {}
        self._last_speak_pipe = None
        self._vision_thread = threading.Thread(target=self._vision.main)
        self._vision_thread.setDaemon(True)
        self._vision_thread.start()
        self._sound_file_dict = {'oclock': 'se_maoudamashii_chime05.wav',
                                 'face': 'se_maoudamashii_onepoint28.wav',
                                 'move': 'se_maoudamashii_onepoint24.wav',
                                 'tired': 'se_maoudamashii_chime05.wav',
                                 'back': 'se_maoudamashii_magical30.wav',
                                 }
        self._applications = [touch_motion, emotional_motion, show_network, connect_network_by_code, speak_time, 
                              shutdown_by_vision, deal_emotion, listen_sound, check_ground,  random_motion,
                              overwrite_direct_command]
        self._ignoring_time = {'mic': 0}

    def get_last_sensor_dict(self):
        return self._sensor_history[-1]

    def execute(self, command):
        '''
        dance, velocity, speak, emotion
        '''
        if 'sound' in command:
            if command['sound'] in self._sound_file_dict:
                utils.play_sound(self._sound_file_dict[command['sound']])
        if 'speak' in command:
            if self._last_speak_pipe:
                self._last_speak_pipe.wait()
            self._last_speak_pipe = utils.speak(command['speak'])

        if 'dance' in command:
            if command['dance'] == 1:
                self._robot_driver.set_velocity(100, 0)
                time.sleep(1)
                self._robot_driver.set_velocity(-100, 0)
                time.sleep(1)
                self._robot_driver.set_velocity(0, 0)
            if command['dance'] == 2:
                self._robot_driver.set_velocity(0, 100)
                time.sleep(1)
                self._robot_driver.set_velocity(0, -100)
                time.sleep(1)
                self._robot_driver.set_velocity(0, 0)
            if command['dance'] == 3:
                self._robot_driver.set_velocity(0, 100)
                time.sleep(0.2)
                self._robot_driver.set_velocity(0, 0)
            if command['dance'] == 4:
                self._robot_driver.set_velocity(0, -100)
                time.sleep(0.2)
                self._robot_driver.set_velocity(0, 0)
            if command['dance'] == 5:
                self._robot_driver.set_velocity(-100, 0)
                time.sleep(1.0)
                self._robot_driver.set_velocity(0, -100)
                time.sleep(0.5)
            if command['dance'] == 6:
                self._robot_driver.set_velocity(-100, 0)
                time.sleep(1.0)
                self._robot_driver.set_velocity(0, 100)
                time.sleep(0.5)

        if 'velocity' in command:
            self._robot_driver.set_velocity(*command['velocity'])
        else:
            self._robot_driver.set_velocity(0)
        if 'emotion' in command:
            # reset all negatives by positive feedback
            if command['emotion'] > 0 and self._emotion.get_balance() < 0:
                self._emotion.reset()
            self._emotion.add_positive(command['emotion'])
        if 'system' in command:
            if command['system'] == 'poweroff':
                self._robot_driver.set_velocity(0, 0)
                os.system('poweroff')

    def get_sensor_data(self):
        sensor_dict = self._sensor.get_sensor_data()
        sensor_dict.update(self._vision.get_sensor_data())
        return sensor_dict

    def get_command(self, sensor_dict):
        '''
        touch_l, touch_r, command_velocity, command_speak, from_start_sec,
        emotion, is_online, oclock_hour
        '''
        #
        # Use cerebrum commands
        #
        command = {}
        #
        # Use cerebellum
        #
        for app in self._applications:
            app(sensor_dict, command, self._sensor_history, self._ignoring_time)

        self._sensor_history.append(sensor_dict)
        return command


def main():
#    utils.play_sound('se_maoudamashii_se_drink02.wav').wait()
#    utils.speak(u'ちびぱいぼっときどうしました！')
    c = Cerebellum()
    while True:
        sensor = c.get_sensor_data()
        print sensor
#        print '%03d %03d' % (abs(sensor['mic_l']), abs(sensor['mic_r']))
        command = c.get_command(sensor)
#        print command
        c.execute(command)
        time.sleep(0.1)

if __name__ == '__main__':
    main()
