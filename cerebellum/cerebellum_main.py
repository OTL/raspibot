#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys, codecs
sys.stdout = codecs.lookup('utf_8')[-1](sys.stdout)

import os
import threading
import time

from rpc_client import CerebrumRpcClient
from sensors import SensorDataCollector
from sensors import Emotion
from chibipibot_driver import ChibiPiBot
import utils
import vision

class Cerebellum(object):

    def __init__(self):
        self._emotion = Emotion()
        self._robot_driver = ChibiPiBot()
        self._sensor = SensorDataCollector(robot_driver=self._robot_driver,
                                           emotion=self._emotion,
                                           cerebrum_getter=CerebrumRpcClient())
        self._last_sensor_dict = self._sensor.get_sensor_data()
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
                                 }

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
        if 'velocity' in command:
            self._robot_driver.set_velocity(*command['velocity'])
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
        if sensor_dict['emotion'] > 3000:
            command['speak'] = u'楽しくなってきた！'
            command['emotion'] = -2000
            command['dance'] = 1
        if sensor_dict['emotion'] < -3000:
#            command['speak'] = u'なんかつまんないなー'
            command['sound'] = 'tired'
            command['emotion'] = 2000
            command['dance'] = 2

        if sensor_dict['is_online'] and not self._last_sensor_dict['is_online']:
            command['speak'] = u'ネットワークに接続したよ'
        if not sensor_dict['is_online'] and self._last_sensor_dict['is_online']:
            command['speak'] = u'ネットワークから切断したみたい'

        if not sensor_dict['is_online'] and 'code' in sensor_dict and sensor_dict['code'] is not None:
            utils.set_wifi_from_string(sensor_dict['code'])

        if sensor_dict['oclock_hour'] is not None and (
            self._last_sensor_dict['oclock_hour'] is None):
            command['speak'] = u'%d時ちょうどになったね' % sensor_dict['oclock_hour']
            command['sound'] = 'oclock'
            command['dance'] = 1
        def check_hour(i):
            if sensor_dict['from_start_sec'] >= i * 60 * 60 and (
                self._last_sensor_dict['from_start_sec'] < i * 60 * 60):
                return i
            return None
        for i in range(5):
            hour = check_hour(i)
            if hour:
                command['speak'] = u'動き出して%d時間たったよ' % hour
                command['dance'] = 1

        if sensor_dict['darkness'] and sensor_dict['touch_l'] and sensor_dict['touch_r']:
            command['speak'] = u'電源を切ります'
            command['system'] = 'poweroff'
        if not command:
            command['emotion'] = -10
        #
        # overwrite by brain
        #
        if sensor_dict['command_velocity']:
            command['velocity'] = sensor_dict['command_velocity']
        if sensor_dict['command_speak']:
            command['speak'] = sensor_dict['command_speak']

        self._last_sensor_dict = sensor_dict
        return command


def main():
    utils.play_sound('se_maoudamashii_se_drink02.wav').wait()
    utils.speak(u'ちびぱいぼっときどうしました！')
    c = Cerebellum()
    while True:
        sensor = c.get_sensor_data()
        print sensor
        command = c.get_command(sensor)
        print command
        c.execute(command)
        time.sleep(0.1)

if __name__ == '__main__':
    main()
