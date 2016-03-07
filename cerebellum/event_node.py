import datetime
import time
import urllib2

import jps
import json


def send_ifttt(event_name):
    urllib2.urlopen('https://maker.ifttt.com/trigger/%s/with/key/d45C-YTPDxBG0pSZ8uE2-T' % event_name).read()


class EventPublisher(object):
    def __init__(self, host='smilerobotics.com'):
        self._sensor_sub = jps.Subscriber('sensor', host=host)
        self._cmd_vel_sub = jps.Subscriber('cmd_vel', self.cmd_vel_callback, host=host)
        self._cmd_vel_sub.spin(use_thread=True)
        self._pub = jps.Publisher('events', host=host)
        self._last_event_time = 0

    def cmd_vel_callback(self, msg):
        self._last_event_time = time.time()

    def main(self):
        for sensor_msg in self._sensor_sub:
            sensor = json.loads(sensor_msg)
            if sensor['mic_r'] > 200 and sensor['mic_l'] > 200:
                self.send_event('loud')
            elif sensor['v_battery'] < 3.4:
                self.send_event('low_battery')

    def send_event(self, event_name):
        now = time.time()
        if now - self._last_event_time > 30:
            send_ifttt(event_name)
            self._pub.publish(json.dumps([{'time': str(datetime.datetime.today()),
                                           'text': event_name}]))
        self._last_event_time = now


def main(host='smilerobotics.com'):
    e = EventPublisher(host=host)
    e.main()

        
if __name__ == '__main__':
    main(host='smilerobotics.com')

