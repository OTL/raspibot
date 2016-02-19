#!/usr/bin/env python
# -*- coding: utf-8 -*-

from geventwebsocket.handler import WebSocketHandler
from gevent import pywsgi
import threading
import datetime
import json
import jps


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
    def __init__(self, callback):
        super(JpsCommandServer, self).__init__()
        self._sensor_sub = jps.Subscriber('sensor', callback)
        self._all_pub = jps.Publisher('')

    def start(self):
        self._server_thread = threading.Thread(target=self._sensor_sub.spin)
        self._server_thread.setDaemon(True)
        self._server_thread.start()

    def update_command(self, command_dict):
        super(JpsCommandServer, self).update_command(command_dict)
        for key, value in command_dict.items():
            self._all_pub.publish('{topic} {data}'.format(topic=key, data=value))


class WebsocketServer(object):
    def command_handle(self, environ, start_response):
        self._ws = environ['wsgi.websocket']
        while True:
            msg = self._ws.receive()
            if msg is None:
                break
            try:
                command = json.loads(msg)
                self._command_sender.update_command(command)
            except ValueError:
                print 'value_error: ' + msg
            send_data = {}
            send_data['sensor'] = self._command_sender.get_sensor_data()
            #send_data['sensor'] = {'face': 2, 'sound': 100}
            #send_data['events'] = self._command_sender.get_events()
            send_data['events'] = [{'time': str(datetime.datetime.today()),
                                    'text': 'found faces!'},
                                   {'time': str(datetime.datetime.today()),
                                    'text': 'loud voice!!'},
                                   ]
            self._ws.send(json.dumps(send_data))

    def myapp(self, environ, start_response):  
        path = environ["PATH_INFO"]
        if path == "/chibipibot":
            return self.command_handle(environ, start_response)
            

    def sensor_callback(self, msg_json):
        if self._ws and not self._ws.closed:
            send_data = {}
            send_data['sensor'] = json.loads(msg_json)
            self._ws.send(json.dumps(send_data))

    def __init__(self, port=9090):
        self._ws = None
        self._command_sender = JpsCommandServer(self.sensor_callback)
        self._command_sender.start()
        # https://github.com/miguelgrinberg/Flask-SocketIO/issues/65
        from gevent import monkey
        monkey.patch_all()
        self._server = pywsgi.WSGIServer(('0.0.0.0', port), self.myapp, 
                                         handler_class=WebSocketHandler)

    def start(self):
        self._server.serve_forever()


if __name__ == '__main__':
    import os
    import time
    import sys
    import signal

    s = WebsocketServer()
    s.start()

