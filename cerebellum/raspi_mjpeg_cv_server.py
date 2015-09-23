# import the necessary packages
from picamera.array import PiRGBArray
from picamera import PiCamera
import time
import sys
import cv2
import numpy as np
import Image

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from SocketServer import ThreadingMixIn
import threading

import StringIO

IMAGE_WIDTH = 320
IMAGE_HEIGHT = 240


class ImageWithLock:

    def __init__(self, img=None):
        self._img = img
        self._lock = threading.Lock()

    def set_image(self, img):
        with self._lock:
            self._img = img

    def get_image(self):
        with self._lock:
            return self._img

image = ImageWithLock()


class MjpegHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        global image
        if self.path.endswith('.mjpg'):
            while True:
                self.send_response(200)
                self.send_header(
                    'Content-type', 'multipart/x-mixed-replace; boundary=--jpgboundary')
                self.end_headers()
                imgRGB = cv2.cvtColor(image.get_image(), cv2.COLOR_BGR2RGB)
                jpg = Image.fromarray(imgRGB)
                tmpFile = StringIO.StringIO()
                jpg.save(tmpFile, 'JPEG')
                self.wfile.write("--jpgboundary")
                self.send_header('Content-type', 'image/jpeg')
                self.send_header('Content-length', str(tmpFile.len))
                self.end_headers()
                jpg.save(self.wfile, 'JPEG')
                time.sleep(0.05)
            return
        if self.path.endswith('.html'):
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write('<html><head></head><body>')
            self.wfile.write('<img src="http://127.0.0.1:8080/cam.mjpg"/>')
            self.wfile.write('</body></html>')
            return


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    pass


def server_thread_proc():
    try:
        server = ThreadedHTTPServer(('', 8080), MjpegHandler)
        print "server started"
        server.serve_forever()
    except KeyboardInterrupt:
        server.socket.close()


def main():
    global image
    # initialize the camera and grab a reference to the raw camera capture
    camera = PiCamera()
    camera.resolution = (IMAGE_WIDTH, IMAGE_HEIGHT)
    camera.framerate = 15
    # allow the camera to warmup
    time.sleep(0.1)
    server_thread = threading.Thread(target=server_thread_proc)
    server_thread.setDaemon(True)
    server_thread.start()

    rawCapture = PiRGBArray(camera, size=(IMAGE_WIDTH, IMAGE_HEIGHT))
    for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
        try:
            #            image.set_image(frame.array)
            img = frame.array
            rawCapture.truncate(0)
            face_cascade = cv2.CascadeClassifier(
                '/usr/share/opencv/haarcascades/haarcascade_frontalface_default.xml')
            eye_cascade = cv2.CascadeClassifier(
                '/usr/share/opencv/haarcascades/haarcascade_eye.xml')
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)
            print faces
            for (x, y, w, h) in faces:
                cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
                roi_gray = gray[y:y + h, x:x + w]
                roi_color = img[y:y + h, x:x + w]
                eyes = eye_cascade.detectMultiScale(roi_gray)
                for (ex, ey, ew, eh) in eyes:
                    cv2.rectangle(roi_color, (ex, ey),
                                  (ex + ew, ey + eh), (0, 255, 0), 2)
            image.set_image(img)
            time.sleep(0.05)
        except KeyboardInterrupt:
            sys.exit(0)


if __name__ == '__main__':
    main()
