#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cv2
import numpy
import threading

from http_server import HttpMjpegServer
from http_server import HttpMjpegHandler
import websocket_server
import jps


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


class JpsImageReceiver:
    def __init__(self):
        self._sub = jps.Subscriber('image', self.callback)
        self.jpeg_image = DataWithLock()

    def spin(self):
        self._sub.spin()

    def callback(self, msg):
        jpg_data = numpy.fromstring(msg, dtype = "uint8")
        self.jpeg_image.set_data(jpg_data)

        
def main():
    jps.launcher.launch_modules(['jps.forwarder', 'websocket_server', 'vision_node'])
    receiver = JpsImageReceiver()
    mjpeg_server = HttpMjpegServer()
    mjpeg_server.start()

    dummy_img = cv2.imread('dummy.jpg')
    receiver.jpeg_image.set_data(cv2.imencode(".jpeg", dummy_img, [int(cv2.IMWRITE_JPEG_QUALITY), 100]))
    HttpMjpegHandler.jpg_image = receiver.jpeg_image
    try:
        receiver.spin()
    except KeyboardInterrupt:
        pass
    mjpeg_server.close()


if __name__ == "__main__":
    main()
