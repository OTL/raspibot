#!/usr/bin/env python
# -*- coding: utf-8 -*-

from geventwebsocket.handler import WebSocketHandler
from gevent import pywsgi
import threading
import json
import jps
import time


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
    def __init__(self, forward_topics, callback):
        super(JpsCommandServer, self).__init__()
        self._forward_topics = forward_topics
        self._callback = callback
        self._all_pub = jps.utils.JsonMultiplePublisher()
        self._subscribers = {}

    def start(self):
        for topic in self._forward_topics:
            self._subscribers[topic] = jps.Subscriber(topic, self._callback(topic))
            self._subscribers[topic].spin(use_thread=True)

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


    def callback(self, topic_name):
        def callback_with_topic_name(msg_json):
            for ws in self._ws.values():
                if not ws.closed:
                    send_data = {}
                    send_data[topic_name] = json.loads(msg_json)
                    try:
                        ws.send(json.dumps(send_data))
                    except:
                        print 'failed to send {}'.format(topic_name)
        return callback_with_topic_name


    def __init__(self, port=9090):
        self._ws = {}
        self._command_sender = JpsCommandServer(['sensor', 'battery', 'events'], self.callback)
        self._command_sender.start()
        # https://github.com/miguelgrinberg/Flask-SocketIO/issues/65
        from gevent import monkey
        monkey.patch_all()
        self._server = pywsgi.WSGIServer(('0.0.0.0', port), self.myapp, 
                                         handler_class=WebSocketHandler)

    def start(self):
        self._server.serve_forever()


def main():
    try:
        s = WebsocketServer()
        s.start()
    except KeyboardInterrupt:
        pass

    
if __name__ == '__main__':
    main()
