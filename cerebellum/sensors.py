import os
import time
import subprocess


class TimeSensor(object)
    
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

    def is_online(self):
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


class SensorDataCollector(object):
    
    def __init__(self, robot_driver, emotion):
        self._robot_driver = robot_driver
        self._time_sensor = virtual_sensor.TimeSensor()
        self._online_sensor = virtual_sensor.OnlineSensor()
        self._emotion = emotion

    def get_sensor_data(self):
        data = {'from_start_sec': self._time_sensor.get_duration_since_start(),
                'emotion': self._emotion.get_balance(),
                'is_online': self.online_sensor.is_online()}
        if self._time_sensor.is_oclock_min():
            data['oclock_hour'] = self._time_sensor.get_current_time().tm_hour
        data.update(self._robot_driver.get_sensor_data())
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
