#!/usr/bin/env python
# -*- coding: utf-8 -*-

import copy
import cv2.cv as cv
import cv2
import numpy
import socket
import threading
import time

from http_server import HttpMjpegServer
from http_server import HttpMjpegHandler
import websocket_server



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
        jpgstring, addr = self._udp.recvfrom(1024 * 64 * 10)
        return numpy.fromstring(jpgstring, dtype = "uint8")
        
    def close(self):
        self._udp.close()


import multiprocessing
import jps
import jps.forwarder


class JpsImageReceiver:
    def __init__(self):
        self._sub = jps.Subscriber('image', self.callback)
        self.jpeg_image = DataWithLock()
        self.image = DataWithLock()

    def spin_once(self):
        self._sub.spin_once()

    def callback(self, msg):
        jpg_data = numpy.fromstring(msg, dtype = "uint8")
        self.jpeg_image.set_data(jpg_data)
        self.image.set_data(cv2.imdecode(jpg_data, 1))
            
        
def main():
    forwarder_process = multiprocessing.Process(target=jps.forwarder.main)
    forwarder_process.start()

    websocket_process = multiprocessing.Process(target=websocket_server.main)
    websocket_process.start()
    receiver = JpsImageReceiver()

    mjpeg_server = HttpMjpegServer()
    mjpeg_server.start()
    face_detector = FaceDetector()
    dummy_img = cv2.imread('dummy.jpg')
    # opencv2.2 hack
    receiver.jpeg_image.set_data(cv2.cv.EncodeImage(".jpeg", cv2.cv.fromarray(dummy_img)))
    receiver.image.set_data(dummy_img)

    HttpMjpegHandler.jpg_image = receiver.jpeg_image
    while True:
        try:
            receiver.spin_once()
#            HttpMjpegHandler.jpg_image = image_with_lock
#            img = cv2.imdecode(image_with_lock.get_data(), 1)
            img = receiver.image.get_data()
#            if cv2.waitKey(10) == 27:
#                break
            faces = face_detector.detect_faces(img)
# TODO:
#            robot_bridge.update_sensor_data({'faces': faces})
            face_detector.draw_face_rectangle(img, faces)
#            cv2.imshow("chibipibot camera", img)
            time.sleep(0.01)
        except KeyboardInterrupt:
            break
            
#    cv2.destroyAllWindows()
#    receiver.close()
    mjpeg_server.close()


if __name__ == "__main__":
    main()
