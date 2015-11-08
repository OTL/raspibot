#!/usr/bin/env python
# -*- coding: utf-8 -*-

import collections
import os
import time
import subprocess
import threading
from mpu_6050 import Mpu6050Reader
from imu import get_rotation


class TimeSensor(object):
    
    def __init__(self):
        self._initial_time = time.localtime()

    def get_duration_since_start(self):
        return time.mktime(time.localtime()) - time.mktime(self._initial_time)

    def get_current_time(self):
        return time.localtime()

    def is_oclock_min(self):
        return self.get_current_time().tm_min == 0


class OnlineSensor(object):

    def __init__(self, server='smilerobotics.com'):
        self._server = server
        self._is_online = self.update_state()
        self._thread = threading.Thread(target=self.update_state_loop)
        self._thread.setDaemon(True)
        self._thread.start()

    def is_online(self):
        return self._is_online

    def update_state_loop(self):
        self._is_online = self.update_state()

    def update_state(self):
        devnull = open(os.devnull, 'wb')
        is_online = subprocess.call(['ping', '-c1', self._server],
                                    stdout=devnull,
                                    stderr=devnull,
                                    ) == 0
        devnull.close()
        return is_online


class Emotion(object):

    def __init__(self):
        self._balance = 0

    def add_positive(self, value=1):
        self._balance = self._balance + value

    def add_negative(self, value=1):
        self._balance = self._balance - value

    def get_balance(self):
        return self._balance

    def reset(self):
        self._balance = 0


class Health(object):

    def __init__(self, initial_value, max_value, min_value):
        self._value = initial_value
        self._max_value = max_value
        self._min_value = min_value
        
    def add(self, value):
        self.set(self._value + value)

    def get(self):
        return self._value

    def set(self, value):
        if value > self._max_value:
            self._value = self._max_value
        elif value < self._min_value:
            self._value = self._min_value
        else:
            self._value = value


class SensorDataCollector(object):
    
    def __init__(self, robot_driver, emotion, health,
                 cerebrum_getter, additional_sensor_source=[]):
        self._robot_driver = robot_driver
        self._time_sensor = TimeSensor()
        self._health = health
        self._online_sensor = OnlineSensor()
        self._emotion = emotion
        self._cerebrum_getter = cerebrum_getter
        self._additional_sensor_source = additional_sensor_source
        self._imu = Mpu6050Reader()
        self._history = collections.deque(maxlen=10)

    def get_sensor_data(self):
        data = {'from_start_sec': self._time_sensor.get_duration_since_start(),
                'emotion': self._emotion.get_balance(),
                'health': self._health.get(),
                'is_online': self._online_sensor.is_online(),
                'command_velocity': None,
                'command_speak': None,
                'oclock_hour': None,
                'rotation': (0.0, 0.0)}
        if self._time_sensor.is_oclock_min():
            data['oclock_hour'] = self._time_sensor.get_current_time().tm_hour
        data.update(self._robot_driver.get_sensor_data())
        if data['is_online']:
            commands = self._cerebrum_getter.get_command(data)
            data.update(commands)

        data['rotation'] = get_rotation(*self._imu.get_acceleration())
        data['acceleration'] = self._imu.get_acceleration()
        data['angular_velocity'] = self._imu.get_angular_velocity()
        data['templerature'] = self._imu.get_temperature()

        def check_flat(rot):
            return abs(rot[0]) < 0.3 and abs(rot[1]) < 0.3
        average_rot = [0.0, 0.0]
        for s in list(self._history):
            average_rot[0] += s['rotation'][0] / len(self._history)
            average_rot[1] += s['rotation'][1] / len(self._history)
        data['average_rotation'] = average_rot
        data['on_flat_ground'] = check_flat(data['average_rotation'])
        for s in self._additional_sensor_source:
            data.update(s.get_sensor_data())
        self._history.append(data)
        return data


def main1():
    on = OnlineSensor()
    print on.is_online()
    on = OnlineSensor(server='dummy')
    print on.is_online()


def main2():
    s = TimeSensor()
    print s.get_duration_since_start()
    print s.is_oclock_min()
    time.sleep(1)
    print s.get_duration_since_start()
    time.sleep(2)
    print s.get_duration_since_start()
    print s.get_current_time()


if __name__ == '__main__':
    main1()
