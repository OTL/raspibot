# based on https://gist.github.com/n3wtron/4624820

import threading

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from SocketServer import ThreadingMixIn
import threading
import StringIO
import os.path
import cv2
import numpy
import jps


class HttpMjpegHandler(BaseHTTPRequestHandler):
    jpg_image = None
    def log_message(self, format, *args):
        return

    def handle_jpeg(self):
        self.send_response(200)
        self.send_header(
            'Content-type', 'multipart/x-mixed-replace; boundary=--jpgboundary')
        self.end_headers()
        try:
            if HttpMjpegHandler.jpg_image is not None and (
                HttpMjpegHandler.jpg_image.get_data() is not None):
                jpg_binary = HttpMjpegHandler.jpg_image.get_data().tostring()
                self.wfile.write("--jpgboundary")
                self.send_header('Content-type', 'image/jpeg')
                self.send_header('Content-length', str(len(jpg_binary)))
                self.end_headers()
                self.wfile.write(jpg_binary)
        except:
            print 'error'

    def handle_file(self):
        path = 'html' + self.path
        if os.path.isfile(path):
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(open('html' + self.path).read())
        else:
            self.send_response(404)

    def do_GET(self):
        if self.path.endswith('.mjpg'):
            while True:
                self.handle_jpeg()
            return
        else:
            self.handle_file()


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    pass


class HttpMjpegServer(object):

    def __init__(self):
        self._server = ThreadedHTTPServer(('', 8088), HttpMjpegHandler)
        
    def start(self):
        server_thread = threading.Thread(target=self._server.serve_forever)
        server_thread.setDaemon(True)
        server_thread.start()

    def close(self):
        print 'close http_server'
        self._server.socket.close()


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
        self._sub = jps.Subscriber('image_processed', self.callback)
        self.jpeg_image = DataWithLock()

    def spin(self):
        self._sub.spin()

    def callback(self, msg):
        jpg_data = numpy.fromstring(msg, dtype = "uint8")
        self.jpeg_image.set_data(jpg_data)


def main():
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
