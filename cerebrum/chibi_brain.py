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
                            requestHandler=RequestHandler, allow_none=True)
server.register_introspection_functions()

def get_command(sensor_dict):
    global face_num
    command = {'command_speak':None, 'command_velocity':None}
    # speak
    if face_num > 0:
        command['command_speak'] = u'こんにちは'
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
            face_cascade = cv2.CascadeClassifier(
                '/usr/share/opencv/haarcascades/haarcascade_frontalface_default.xml')
            eye_cascade = cv2.CascadeClassifier(
                '/usr/share/opencv/haarcascades/haarcascade_eye.xml')
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
