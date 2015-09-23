#!/usr/bin/env python
# -*- coding: utf-8 -*-

import utils
import time
from rpc_client import CerebrumRpcClient
from sensors import SensorDataCollector
from sensors import Emotion
from chibipibot_driver import ChibiPiBot

class Cerebellum(object):

    def __init__(self):
        self._emotion = Emotion()
        self._robot_driver = ChibiPiBot()
        self._sensor = SensorDataCollector(robot_driver=self._robot_driver,
                                           emotion=self._emotion,
                                           cerebrum_getter=CerebrumRpcClient())
        self._last_sensor_dict = self._sensor.get_sensor_data()
        self._command = {}
        self._last_speak_pipe = None

    def execute(self, command):
        '''
        dance, velocity, speak, emotion
        '''
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
        if 'velocity' in command:
            self._robot_driver.set_velocity(*command['velocity'])
        if 'emotion' in command:
            self._emotion.add_positive(command['emotion'])


    def get_command(self):
        '''
        touch_l, touch_r, command_velocity, command_speak, from_start_sec,
        emotion, is_online, oclock_hour
        '''
        sensor_dict = self._sensor.get_sensor_data()
        #
        # Use cerebrum commands
        #
        command = {}
        used_cerebrum = False
        if sensor_dict['command_velocity']:
            command['velocity'] = sensor_dict['command_velocity']
            used_cerebrum = True
        if sensor_dict['command_speak']:
            command['speak'] = sensor_dict['command_speak']
            used_cerebrum = True
        if used_cerebrum:
            return
        #
        # Use cerebellum
        #
        if sensor_dict['touch_l'] and sensor_dict['touch_r']:
            command['speak'] = u'おさないでー'
            command['velocity'] = (-100, 0)
            command['emotion'] = -1000
        elif sensor_dict['touch_l']:
            command['velocity'] = (0, 100)
            command['speak'] = u'左へ曲がるよ'
            command['emotion'] = 1000
        elif sensor_dict['touch_r']:
            command['velocity'] = (0, -100)
            command['speak'] = u'右へ曲がるよ'
            command['emotion'] = 1000
        
        if sensor_dict['emotion'] > 3000:
            command['speak'] = u'楽しくなってきた！'
            command['emotion'] = -2000
            command['dance'] = 1
        if sensor_dict['emotion'] < -3000:
            command['speak'] = u'なんかつまんないなー'
            command['emotion'] = 2000
            command['dance'] = 2

        if sensor_dict['is_online'] and not self._last_sensor_dict['is_online']:
            command['speak'] = u'ネットワークに接続したよ'
        if not sensor_dict['is_online'] and self._last_sensor_dict['is_online']:
            command['speak'] = u'ネットワークから切断したみたい'

        if sensor_dict['oclock_hour'] is not None and (
            self._last_sensor_dict['oclock_hour'] is None):
            command['speak'] = u'%d時ちょうどになったね' % sensor_dict['oclock_hour']
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

        self._last_sensor_dict = sensor_dict
        return command


def main():
    c = Cerebellum()
    while True:
        command = c.get_command()
        print command
        c.execute(command)
        time.sleep(0.1)

if __name__ == '__main__':
    main()
