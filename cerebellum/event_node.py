import datetime
import time
import urllib2

import jps
import json


def send_ifttt(event_name):
    urllib2.urlopen('https://maker.ifttt.com/trigger/%s/with/key/d45C-YTPDxBG0pSZ8uE2-T' % event_name).read()


class EventPublisher(object):
    def __init__(self, host='smilerobotics.com'):
        self._host = host
        self._sensor_sub = jps.Subscriber('sensor', host=host)
        self._pub = jps.Publisher('events', host=host)
        self._last_event_info = {}
        self._subscribers = []
        self._subscribers.append(self.set_event_ignore_topic(['loud'], 'cmd_vel', 5))
        self._subscribers.append(self.set_event_ignore_topic(['loud'], 'sound', 5))
        def check_loud(sensor):
            return sensor['mic_r'] > 200 and sensor['mic_l'] > 200
        def check_battery(sensor):
            return sensor['v_battery'] < 3.4
        def check_charge(sensor):
            return sensor['v_charge'] > 4.0
        def check_discharge(sensor):
            return sensor['v_charge'] < 3.0
        def check_hover(sensor):
            return sensor['photo_r'] > 2000 and  sensor['photo_l'] > 2000
        self._check_sensor_functions = {
            'loud': check_loud,
            'low_battery': check_battery,
            'charge': check_charge,
            'discharge': check_discharge,
            'hover': check_hover,
        }

    def set_event_ignore_topic(self, events, topic, ignore_duration):
        sub = jps.Subscriber(topic, self.set_event_ignore_callback(events, ignore_duration), host=self._host)
        sub.spin(use_thread=True)
        for event in events:
            self._last_event_info[event] = [time.time(), 0]
        return sub

    def set_ignore_info(self, event, timestamp, duration):
        self._last_event_info[event] = [timestamp,  duration]
        
    def set_event_ignore_callback(self, events, ignore_duration):
        def ignore_callback(msg):
            now = time.time()
            for event in events:
                self.set_ignore_info(event, now, ignore_duration)
        return ignore_callback

    def main(self):
        last_sensor = json.loads(self._sensor_sub.next())
        for sensor_msg in self._sensor_sub:
            sensor = json.loads(sensor_msg)
            for event, check_func in self._check_sensor_functions.items():
                if check_func(sensor) and not check_func(last_sensor):
                    self.send_event_if_not_ignore_time(event)
            last_sensor = sensor

    def send_event_if_not_ignore_time(self, event_name):
        now = time.time()
        ignore_start_time = 0
        ignore_duration = 0
        if event_name in self._last_event_info:
            ignore_start_time = self._last_event_info[event_name][0]
            ignore_duration = self._last_event_info[event_name][1]
        if now - ignore_start_time > ignore_duration:
            send_ifttt(event_name)
            self._pub.publish(json.dumps([{'time': str(datetime.datetime.today()),
                                           'text': event_name}]))
            self._last_event_info[event_name] = [now, 1]


def main(host='smilerobotics.com'):
    try:
        e = EventPublisher(host=host)
        e.main()
    except KeyboardInterrupt:
        pass

        
if __name__ == '__main__':
    main(host='smilerobotics.com')

