#!/usr/bin/env python
# -*- coding: utf-8 -*-

from geventwebsocket.handler import WebSocketHandler
from gevent import pywsgi
import threading

class WebsocketServer(object):
    def command_handle(self, environ, start_response):
        ws = environ['wsgi.websocket']
        self._command_sender.update_command(
            {'command_speak': u'接続開始です'})
        while True:
            msg = ws.receive()
            if msg is None:
                break
            if msg == 'go_forward':
                self._command_sender.update_command(
                    {'command_velocity': (100, 0)}) 
            elif msg == 'go_backward':
                self._command_sender.update_command(
                    {'command_velocity': (-100, 0)})
            elif msg == 'go_left':
                self._command_sender.update_command(
                    {'command_velocity': (0, 100)})
            elif msg == 'go_right':
                self._command_sender.update_command(
                    {'command_velocity': (0, -100)})
            elif msg == 'go_stop':
                self._command_sender.update_command(
                    {'command_velocity': (0, 0)})
            elif msg == 'say_move':
                self._command_sender.update_command(
                    {'command_speak': u'どいてください'})
            elif msg == 'say_hello':
                self._command_sender.update_command(
                    {'command_speak': u'こんにちは'})
        self._command_sender.update_command(
            {'command_speak': u'また遊んでね'})

    def myapp(self, environ, start_response):  
        path = environ["PATH_INFO"]
        if path == "/chibipibot":  
            return self.command_handle(environ, start_response)

    def __init__(self, command_sender, port=9090):
        # https://github.com/miguelgrinberg/Flask-SocketIO/issues/65
        from gevent import monkey
        monkey.patch_all()
        self._command_sender = command_sender
        self._server = pywsgi.WSGIServer(('0.0.0.0', port), self.myapp, 
                                         handler_class=WebSocketHandler)

    def start(self):
        self._server.start()
