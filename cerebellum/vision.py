from picamera.array import PiRGBArray
from picamera import PiCamera

import exceptions
import threading
import time
import cv2
import socket
import numpy as np
import zbar

IMAGE_WIDTH = 320
IMAGE_HEIGHT = 240

class ImageJpegUdpSender(object):

    def __init__(self, host, port):
        self._host = host
        self._port = port
        self._udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send_image(self, cv_image, quality=95):
        is_success, encoded_image = cv2.imencode(".jpeg", cv_image,
                                                 [int(cv2.IMWRITE_JPEG_QUALITY), quality])
        if is_success:
            self._udp.sendto(encoded_image.tostring(), (self._host, self._port))
            return True
        else:
            return False

    def close(self):
        self._udp.close()


class DarknessRecognizer(object):

    def is_dark(self, image, v_threshold=50, area_threshold=50):
        dark_min = np.array([0, 0, 0], np.uint8)
        dark_max = np.array([360, 255, v_threshold], np.uint8)
        hsv_img = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        dark_pixels = cv2.inRange(hsv_img, dark_min, dark_max)
        num_dark_pixels = cv2.countNonZero(dark_pixels)
        if num_dark_pixels > area_threshold * IMAGE_WIDTH * IMAGE_HEIGHT / 100:
            return True
        return False


class CodeReader(object):

    def decode(self, img):
        imgray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        raw = str(imgray.data)
        scanner = zbar.ImageScanner()
#        scanner.parse_config('enable')
        scanner.set_config(zbar.Symbol.NONE, zbar.Config.ENABLE, 0)
        scanner.set_config(zbar.Symbol.QRCODE, zbar.Config.ENABLE, 1)
#        scanner.set_config(zbar.Symbol.CODE128, zbar.Config.ENABLE, 1)
#        scanner.set_config(zbar.Symbol.ISBN13, zbar.Config.ENABLE, 1)
        image_zbar = zbar.Image(imgray.shape[1], imgray.shape[0], 'Y800', raw)
        scanner.scan(image_zbar)
        for symbol in image_zbar:
            print '==========='
            print 'decoded', symbol.type, 'symbol', '"%s"' % symbol.data
            print '============'
            return symbol.data
        return None


class VisionSensor(object):

    def __init__(self, image_width=IMAGE_WIDTH, image_height=IMAGE_HEIGHT):
        # initialize the camera and grab a reference to the raw camera capture
        self._camera = PiCamera()
        self._camera.resolution = (image_width, image_height)
        self._camera.framerate = 15
        self._rawCapture = PiRGBArray(self._camera, size=(image_width, image_height))
        # allow the camera to warmup
        time.sleep(0.1)
    
        self._jpeg_sender = ImageJpegUdpSender('smilerobotics.com', 12345)
        self._darkness_recognizer = DarknessRecognizer()
        self._code_reader = CodeReader()
        self._sensor_data = {'darkness': False}
        self._lock = threading.Lock()
        self._is_stopping = False

    def stop(self):
        self._is_stopping = True

    def main(self):
        for frame in self._camera.capture_continuous(self._rawCapture,
                                                     format="bgr", use_video_port=True):
            if self._is_stopping:
                break
            try:
#                print 'cap'
                img = frame.array
                self._rawCapture.truncate(0)
#                if not self._jpeg_sender.send_image(img):
#                    print 'failed to encode image'
                with self._lock:
                    cv2.imwrite('hoge.jpg', img)
                    self._sensor_data['darkness'] = self._darkness_recognizer.is_dark(img)
                    self._sensor_data['code'] = self._code_reader.decode(img)
                    print self._sensor_data
                time.sleep(0.01)
            except KeyboardInterrupt, exceptions.AttributeError:
                self._jpeg_sender.close()
                break

    def get_sensor_data(self):
        with self._lock:
            return self._sensor_data


if __name__ == '__main__':
    v = VisionSensor()
    v.main()
