#!/usr/bin/env python
# -*- coding: utf-8 -*-

import copy
import cv2.cv as cv
import cv2
import numpy
import socket
import threading
import time

from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler

from http_server import HttpMjpegServer
from http_server import HttpMjpegHandler
from websocket_server import WebsocketServer

# Restrict to a particular path.
class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)

class RpcCommandServer(object):
    def __init__(self, port=12346):
        self._sensor_dict = {}
        self._server = SimpleXMLRPCServer(("0.0.0.0", port),
                                          logRequests=False,
                                          requestHandler=RequestHandler, allow_none=True)
        self._server.register_introspection_functions()
        self._server.register_function(self.get_command)
        self._command = {}

    def start(self):
        self._server_thread = threading.Thread(target=self._server.serve_forever)
        self._server_thread.setDaemon(True)
        self._server_thread.start()

    def update_sensor_data(self, sensor_dict):
        self._sensor_dict.update(sensor_dict)

    def update_command(self, command_dict):
        self._command.update(command_dict)

    def get_command(self, cerebellum_sensor_dict):
        # speak
        command = copy.copy(self._command)
        # clear
        self._command = {}
        if 'faces' in self._sensor_dict:
            if len(self._sensor_dict['faces']) == 1:
                command['command_speak'] = u'こんにちは'
            elif len(self._sensor_dict['faces']) > 1:
                command['command_speak'] = u'みんなでどうしたの'
        return command

class DataWithLock():
    def __init__(self, data=None):
        self._lock = threading.Lock()
        self._data = data

    def set_data(self, data):
        with self._lock:
            self._data = data

    def get_data(self):
        with self._lock:
            return self._data

class FaceDetector(object):
    
    def __init__(self):
        self._face_cascade = cv2.CascadeClassifier(
            '/usr/share/opencv/haarcascades/haarcascade_frontalface_default.xml')

    def detect_faces(self, img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = self._face_cascade.detectMultiScale(gray, 1.3, 5)
        return faces

    def draw_face_rectangle(self, img, faces):
        for (x, y, w, h) in faces:
            cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)


class JpegUdpReceiver(object):
    
    def __init__(self, port=12345):
        self._udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._udp.bind(("0.0.0.0", port))

    def receive_jpeg(self):
        '''block until get data'''
        jpgstring, addr = self._udp.recvfrom(1024 * 64)
        return numpy.fromstring(jpgstring, dtype = "uint8")
        
    def close(self):
        self._udp.close()


if __name__ == "__main__":
    rpc_server = RpcCommandServer()
    rpc_server.start()
    receiver = JpegUdpReceiver()
    face_detector = FaceDetector()
    mjpeg_server = HttpMjpegServer()
    mjpeg_server.start()
    websocket_server = WebsocketServer(rpc_server)
    websocket_server.start()
    image_with_lock = DataWithLock()
    while True:
        try:
            image_with_lock.set_data(receiver.receive_jpeg())
            HttpMjpegHandler.jpg_image = image_with_lock
            img = cv2.imdecode(image_with_lock.get_data(), 1)
            if cv2.waitKey(10) == 27:
                break
            faces = face_detector.detect_faces(img)
            rpc_server.update_sensor_data({'faces': faces})
            face_detector.draw_face_rectangle(img, faces)
            cv2.imshow("chibipibot camera", img)
            time.sleep(0.01)
        except KeyboardInterrupt:
            break
            
    cv2.destroyAllWindows()
    receiver.close()
    mjpeg_server.close()
