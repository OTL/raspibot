#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys, codecs
sys.stdout = codecs.lookup('utf_8')[-1](sys.stdout)

import os
import random
import threading
import time

from rpc_client import CerebrumRpcClient
from sensors import SensorDataCollector
from sensors import Emotion, Health
from chibipibot_driver import ChibiPiBot
import utils
import vision
import brain


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
#    if not sensor_dict['is_online'] and sensor_dict.get('code'):
    if sensor_dict.get('code'):
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

def deal_health(sensor_dict, command, history, ignoring_time):
    TIRED_HEALTH=-5000
    if sensor_dict['health'] < TIRED_HEALTH and history[-1]['health'] >= TIRED_HEALTH:
        command['speak'] = u'疲れてきちゃった'
        # tired more, to avoid chattering
        command['health'] = -1000


def listen_sound(sensor_dict, command, history, ignoring_time):
    if 'mic' not in ignoring_time:
        ignoring_time['mic'] = sensor_dict['from_start_sec']
    if ignoring_time['mic'] < sensor_dict['from_start_sec']:
        if sensor_dict.get('mic_r') and sensor_dict.get('mic_l'):
            if sensor_dict.get('mic_r') > 100 and sensor_dict.get('mic_l') > 100:
                command['velocity'] = (80, 0)
                command['speak'] = u'はいはい'
                ignoring_time['mic'] = sensor_dict['from_start_sec'] + 2
            elif sensor_dict.get('mic_r') > 60 and sensor_dict.get('mic_l') > 60:
                if sensor_dict.get('mic_r') - 10 > sensor_dict.get('mic_l'):
                    command['velocity'] = (0, 80)
                    ignoring_time['mic'] = sensor_dict['from_start_sec'] + 2
                elif sensor_dict.get('mic_r') < sensor_dict.get('mic_l') - 10:
                    command['velocity'] = (0, -80)
                    ignoring_time['mic'] = sensor_dict['from_start_sec'] + 2


def check_ground(sensor_dict, command, history, ignoring_time):
    if not sensor_dict['on_flat_ground'] and history[-1]['on_flat_ground']:
        command['speak'] = u'うわあ'
    if sensor_dict['on_flat_ground'] and not history[-1]['on_flat_ground']:
        command['speak'] = u'ふぅ'
    if abs(sensor_dict['rotation'][0]) > 0.3 or abs(sensor_dict['rotation'][1]) > 0.3:
        return
    if 'photo_r' in sensor_dict and 'photo_l' in sensor_dict:
        is_air_l = sensor_dict['photo_l'] > 2000
        is_air_r = sensor_dict['photo_r'] > 2000
        if is_air_l and is_air_r:
            rand = random.random()
            if rand < 0.5:
                command['dance'] = 5
            else:
                command['dance'] = 6
            command['sound'] = 'back'
        elif is_air_l:
            command['dance'] = 5
            command['sound'] = 'back'
        elif is_air_r:
            command['dance'] = 6
            command['sound'] = 'back'


def random_motion(sensor_dict, command, history, ignoring_time):
    if not sensor_dict['on_flat_ground']:
        return

    if 'velocity' not in command:
        rand = random.random()
        rate = 0.05
        if sensor_dict['emotion'] < -2000:
            rate *= 2.0
        if sensor_dict['health'] < -5000:
            rate *= 0.1
        elif sensor_dict['health'] < -3000:
            rate *= 0.5
        if rand < rate:
            command['velocity'] = (80, 0)
        elif rand < rate * 2.5:
            command['velocity'] = (0, 80)
        elif rand < rate * 4.0:
            command['velocity'] = (0, -80)

def overwrite_direct_command(sensor_dict, command, history, ignoring_time):
    if sensor_dict['command_velocity']:
        command['velocity'] = sensor_dict['command_velocity']
    if sensor_dict['command_speak']:
        command['speak'] = sensor_dict['command_speak']


def stopper(sensor_dict, command, history, ignoring_time):
    if 'velocity' not in command:
        command['velocity'] = (0.0, 0.0)


### drivers
class CommandDriver(object):
    def __init__(self, driver, emotion, health):
        self._robot_driver = driver
        self._emotion = emotion
        self._health = health
        self._sound_file_dict = {'oclock': 'se_maoudamashii_chime05.wav',
                                 'face': 'se_maoudamashii_onepoint28.wav',
                                 'move': 'se_maoudamashii_onepoint24.wav',
                                 'tired': 'se_maoudamashii_chime05.wav',
                                 'back': 'se_maoudamashii_magical30.wav',
                                 }
        self._last_speak_pipe = None

    def play_sound(self, sound_id):
        if sound_id in self._sound_file_dict:
            utils.play_sound(self._sound_file_dict[sound_id])

    def speak(self, speak_command):
        if self._last_speak_pipe:
            self._last_speak_pipe.wait()
        self._last_speak_pipe = utils.speak(speak_command)

    def dance(self, dance_id):
        if dance_id == 1:
            self._robot_driver.set_velocity(100, 0)
            time.sleep(1)
            self._robot_driver.set_velocity(-100, 0)
            time.sleep(1)
            self._robot_driver.set_velocity(0, 0)
        if dance_id == 2:
            self._robot_driver.set_velocity(0, 100)
            time.sleep(1)
            self._robot_driver.set_velocity(0, -100)
            time.sleep(1)
            self._robot_driver.set_velocity(0, 0)
        if dance_id == 3:
            self._robot_driver.set_velocity(0, 100)
            time.sleep(0.2)
            self._robot_driver.set_velocity(0, 0)
        if dance_id == 4:
            self._robot_driver.set_velocity(0, -100)
            time.sleep(0.2)
            self._robot_driver.set_velocity(0, 0)
        if dance_id == 5:
            self._robot_driver.set_velocity(-100, 0)
            time.sleep(1.0)
            self._robot_driver.set_velocity(0, -100)
            time.sleep(0.5)
        if dance_id == 6:
            self._robot_driver.set_velocity(-100, 0)
            time.sleep(1.0)
            self._robot_driver.set_velocity(0, 100)
            time.sleep(0.5)

    def move_by_velocity(self, vel_command):
        self._robot_driver.set_velocity(*vel_command)

    def tired_by_velocity(self, vel_command):
        vel = abs(vel_command[0]) + abs(vel_command[1])
        if vel < 50:
            self._health.add(10)
        else:
            self._health.add(-abs(vel_command[0]) - abs(vel_command[1]))

    def deal_emotion(self, emotion_value):
        # reset all negatives by positive feedback
        if emotion_value > 0 and self._emotion.get_balance() < 0:
            self._emotion.reset()
        self._emotion.add_positive(emotion_value)

    def deal_health(self, health_value):
        self._health.add(health_value)

    def system_command(self, command):
        if command == 'poweroff':
            self._robot_driver.set_velocity(0, 0)
            os.system('poweroff')
        elif command == 'exit':
            self._robot_driver.set_velocity(0, 0)
            sys.exit(0)


class ChibiPiBotCerebellum(object):
    def __init__(self):
        self._robot_driver = ChibiPiBot()
        initial_sensor = self._robot_driver.get_sensor_data()
        if initial_sensor['touch_r'] and initial_sensor['touch_l']:
            utils.speak(u'デバッグモードで起動します').wait()
            sys.exit(0)
        self._emotion = Emotion()
        self._health = Health(0, 0, -10000)
        self._vision = vision.VisionSensor()
        self._rpc_client = CerebrumRpcClient()
        self._sensor = SensorDataCollector(robot_driver=self._robot_driver,
                                           emotion=self._emotion,
                                           health=self._health,
                                           cerebrum_getter=self._rpc_client,
                                           additional_sensor_source=[self._vision])
        self._vision_thread = threading.Thread(target=self._vision.main)
        self._vision_thread.setDaemon(True)
        self._vision_thread.start()

        self._command_driver = CommandDriver(self._robot_driver, self._emotion,
                                             self._health)
        self._cerebellum = brain.Cerebellum(self._sensor,
                                      {'sound': [self._command_driver.play_sound],
                                       'speak': [self._command_driver.speak],
                                       'dance': [self._command_driver.dance],
                                       'velocity': [self._command_driver.move_by_velocity,
                                                    self._command_driver.tired_by_velocity,
                                                    ],
                                       'emotion': [self._command_driver.deal_emotion],
                                       'health': [self._command_driver.deal_health],
                                       'system': [self._command_driver.system_command],
                                       },
                                      [touch_motion, emotional_motion, show_network, connect_network_by_code, speak_time,
                                       shutdown_by_vision, deal_emotion, deal_health, listen_sound, check_ground,  random_motion,
                                       overwrite_direct_command, stopper])

    def get_sensor_and_execute(self):
        self._cerebellum.get_sensor_and_execute()

    def close(self):
        self._vision.stop()
        self._rpc_client.stop()
        self._robot_driver.stop()


def main():
#    utils.play_sound('se_maoudamashii_se_drink02.wav').wait()
#    utils.speak(u'ちびぱいぼっときどうしました！')
    c = ChibiPiBotCerebellum()
    try:
        while True:
            c.get_sensor_and_execute()
            time.sleep(0.1)
    except KeyboardInterrupt:
        c.close()

if __name__ == '__main__':
    utils.speak(u'IPアドレスは%s' % utils.get_ip_address_string()).wait()
    main()
