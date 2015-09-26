# based on https://gist.github.com/n3wtron/4624820

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from SocketServer import ThreadingMixIn
import threading
import StringIO
import os.path

class HttpMjpegHandler(BaseHTTPRequestHandler):
    jpg_image = None
    def log_message(self, format, *args):
        return

    def handle_jpeg(self):
        self.send_response(200)
        self.send_header(
            'Content-type', 'multipart/x-mixed-replace; boundary=--jpgboundary')
        self.end_headers()
        if HttpMjpegHandler.jpg_image.get_data() is not None:
            jpg_binary = HttpMjpegHandler.jpg_image.get_data().tostring()
            self.wfile.write("--jpgboundary")
            self.send_header('Content-type', 'image/jpeg')
            self.send_header('Content-length', str(len(jpg_binary)))
            self.end_headers()
            self.wfile.write(jpg_binary)

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
        self._server.socket.close()

