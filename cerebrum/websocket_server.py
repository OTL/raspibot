#!/usr/bin/env python
# -*- coding: utf-8 -*-

from geventwebsocket.handler import WebSocketHandler
from gevent import pywsgi
import threading
import datetime
import json
import jps
import urllib2
import time


def send_ifttt(event_name):
    urllib2.urlopen('https://maker.ifttt.com/trigger/%s/with/key/d45C-YTPDxBG0pSZ8uE2-T' % event_name).read()


class CommandServer(object):
    def __init__(self, port=12346):
        self._sensor_dict = {}
        self._command = {}

    def update_sensor_data(self, sensor_dict):
        self._sensor_dict.update(sensor_dict)

    def update_command(self, command_dict):
        self._command.update(command_dict)

    def get_sensor_data(self):
        return self._sensor_dict

    def start(self):
        pass


class JpsCommandServer(CommandServer):
    def __init__(self, callback, battery_callback):
        super(JpsCommandServer, self).__init__()
        self._sensor_sub = jps.Subscriber('sensor', callback)
        self._battery_sub = jps.Subscriber('battery', battery_callback)
        self._all_pub = jps.utils.JsonMultiplePublisher()

    def start(self):
        self._sensor_sub.spin(use_thread=True)
        self._battery_sub.spin(use_thread=True)

    def update_command(self, command_dict):
        super(JpsCommandServer, self).update_command(command_dict)
        self._all_pub.publish(json.dumps(command_dict))


class WebsocketServer(object):
    def command_handle(self, environ, start_response):
        ws = environ['wsgi.websocket']
        self._ws[environ['REMOTE_ADDR']] = ws
        while True:
            msg = ws.receive()
            if msg is None:
                break
            try:
                command = json.loads(msg)
                self._command_sender.update_command(command)
            except ValueError:
                print 'value_error: ' + msg

    def myapp(self, environ, start_response):  
        path = environ["PATH_INFO"]
        if path == "/chibipibot":
            return self.command_handle(environ, start_response)
            

    def send_event(self, event_name, send_data):
        now = time.time()
        if now - self._last_event_time > 30:
            send_ifttt(event_name)
            send_data['events'].append({'time': str(datetime.datetime.today()),
                                        'text': event_name})
            self._last_event_time = now
            #self._last_event = event_name
        
    def sensor_callback(self, msg_json):
        for ws in self._ws.values():
            if not ws.closed:
                send_data = {}
                send_data['sensor'] = json.loads(msg_json)
                send_data['events'] = []
                try:
                    if send_data['sensor']['mic_r'] > 200:
                        self.send_event('loud', send_data)
                    elif send_data['sensor']['v_battery'] < 3.4:
                        self.send_event('low_battery', send_data)
                    ws.send(json.dumps(send_data))
                except KeyError as e:
                    print e

    def battery_callback(self, msg_json):
        for ws in self._ws.values():
            if not ws.closed:
                send_data = {}
                send_data['battery'] = json.loads(msg_json)
                try:
                    ws.send(json.dumps(send_data))
                except:
                    print 'failed to send battery'


    def __init__(self, port=9090):
        self._last_event_time = 0.0
        self._ws = {}
        self._command_sender = JpsCommandServer(self.sensor_callback, self.battery_callback)
        self._command_sender.start()
        # https://github.com/miguelgrinberg/Flask-SocketIO/issues/65
        from gevent import monkey
        monkey.patch_all()
        self._server = pywsgi.WSGIServer(('0.0.0.0', port), self.myapp, 
                                         handler_class=WebSocketHandler)

    def start(self):
        self._server.serve_forever()


def main():
    s = WebsocketServer()
    s.start()
    
if __name__ == '__main__':
    main()
