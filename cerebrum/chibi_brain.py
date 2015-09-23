#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cv2.cv as cv
import cv2
import numpy
import socket
import threading

from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler

# Restrict to a particular path.
class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)

# Create server
server = SimpleXMLRPCServer(("0.0.0.0", 12346),
                            requestHandler=RequestHandler)
server.register_introspection_functions()

def get_command(sensor_dict):
    global face_num
    command = {'speak':u'', 'velocity':(0, 0)}
    speach = u''
    # speak
    if face_num > 0:
        speach = u'こんにちは'
    elif sensor_dict['touch_l'] and sensor_dict['touch_r']:
        speach = u'おさないでー'
    elif sensor_dict['touch_l'] or sensor_dict['touch_r']:
        speach = u'どーもどーも'
    vel = (0, 0)
    if face_num > 0:
        vel = (100, 0)
    elif sensor_dict['touch_l'] and sensor_dict['touch_r']:
        vel = (-100, 0)
    elif sensor_dict['touch_l']:
        vel = (0, 100)
    elif sensor_dict['touch_r']:
        vel = (0, -100)
    command['speak'] = speach
    command['velocity'] = vel
    return command

server.register_function(get_command)
server_thread = threading.Thread(target=server.serve_forever)
server_thread.setDaemon(True)
server_thread.start()

face_num = 0

if __name__ == "__main__":
    cv.NamedWindow("serverCAM", 1)
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.bind(("0.0.0.0", 12345))
    buff = 1024
    while True:
        try:
            jpgstring, addr = udp.recvfrom(buff * 64)
            print 'receive'
            narray = numpy.fromstring(jpgstring, dtype = "uint8")
            img = cv2.imdecode(narray,1)
            if cv.WaitKey(10) == 27:
                break
            face_cascade = cv2.CascadeClassifier('/usr/share/opencv/haarcascades/haarcascade_frontalface_default.xml')
            eye_cascade = cv2.CascadeClassifier('/usr/share/opencv/haarcascades/haarcascade_eye.xml')
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)
            print faces
            face_num = len(faces)
            for (x,y,w,h) in faces:
                cv2.rectangle(img, (x,y), (x+w,y+h), (255,0,0), 2)
                roi_gray = gray[y:y+h, x:x+w]
                roi_color = img[y:y+h, x:x+w]
                eyes = eye_cascade.detectMultiScale(roi_gray)
                for (ex,ey,ew,eh) in eyes:
                    cv2.rectangle(roi_color,(ex,ey),(ex+ew,ey+eh),(0,255,0),2)
            cv2.imshow("serverCAM", img)

        except KeyboardInterrupt:
            break
            
    cv.DestroyAllWindows()
    udp.close()
