# import the necessary packages
from picamera.array import PiRGBArray
from picamera import PiCamera

import pickle
import time
import cv2
import cv2.cv as cv
import socket
import numpy as np


IMAGE_WIDTH = 320
IMAGE_HEIGHT = 240


def main():
    # initialize the camera and grab a reference to the raw camera capture
    camera = PiCamera()
    camera.resolution = (IMAGE_WIDTH, IMAGE_HEIGHT)
    camera.framerate = 15
    # allow the camera to warmup
    time.sleep(0.1)

    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    rawCapture = PiRGBArray(camera, size=(IMAGE_WIDTH, IMAGE_HEIGHT))
    for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
        try:
            img = frame.array
            rawCapture.truncate(0)
            is_success, encoded_image = cv2.imencode(".jpeg", img,
                                                     [int(cv2.IMWRITE_JPEG_QUALITY), 95])
            if is_success:
                udp.sendto(encoded_image.tostring(),
                           ("smilerobotics.com", 12345))
                print 'sent an image'
            else:
                print 'failed to encode'
            time.sleep(0.05)
        except KeyboardInterrupt:
            udp.close()
            break


if __name__ == '__main__':
    main()
