#!/usr/bin/env python

import json
import time
import math

import jps
import cv2
import numpy as np

def standardize_by_size(x, y, area, img):
    image_width, image_height, _ = img.shape
    center_x = image_width / 2
    center_y = image_height / 2
    return (float(x - center_x) / image_width,
            float(y - center_y) / image_height,
            float(area) / (image_width * image_height))


class ColorExtract(object):
    def __init__(self, host='smilerobotics.com'):
        self._color_pub = jps.Publisher('found_object', host=host)

    def get_colored_area(self, cv_image, lower, upper):
        hsv_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2HSV)
        mask_image = cv2.inRange(hsv_image, lower, upper)
        _, thresh = cv2.threshold(mask_image, 50, 255, cv2.THRESH_BINARY)
        cnts, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL,
                                   cv2.CHAIN_APPROX_SIMPLE)
        if len(cnts) == 0:
            return (0, 0, 0, 0)
        areas = [cv2.contourArea(c) for c in cnts]
        max_index = np.argmax(areas)
        return cv2.boundingRect(cnts[max_index])
        
    def callback(self, cv_image, out_image):
        x, y, w, h = self.get_colored_area(
            cv_image, np.array([150, 40, 10]), np.array([180, 255, 255]))
        area = w * h
        if area > 1000:
            x_rate, y_rate, area_rate = standardize_by_size(x + w/2, y + h/2, area, cv_image)
            cv2.rectangle(out_image, (x, y), (x + w, y + h), (255, 0, 0), 2)
            self._color_pub.publish(json.dumps({
                        'type': 'red',
                        'x': x_rate,
                        'y': y_rate,
                        'area': area_rate}))

class TargetFollower(object):
    def __init__(self, topic):
        self._vel_pub = jps.Publisher('cmd_vel', host=host)
        self._sub = jps.Subscriber(topic, self.callback)
        self._target = None

    def callback(self, msg):
        self._target = json.loads(msg)

    def main(self):
        while True:
            self._sub.spin_once()
            x_y_area = self._target
            if x_y_area is None:
                self._vel_pub.publish(json.dumps({'x': 0, 'theta': 0}))
                return

            x_rate = x_y_area['x']
            area_rate = x_y_area['area']
            if x_rate < -0.4:
                self._vel_pub.publish(json.dumps({'x': 0, 'theta': 50}))
            elif x_rate < -0.2:
                self._vel_pub.publish(json.dumps({'x': 0, 'theta': 30}))
            elif x_rate > 0.4:
                self._vel_pub.publish(json.dumps({'x': 0, 'theta': -50}))
            elif x_rate > 0.2:
                self._vel_pub.publish(json.dumps({'x': 0, 'theta': -30}))
            elif area_rate < 0.01:
                self._vel_pub.publish(json.dumps({'x': 50, 'theta': 0}))
            elif area_rate > 0.05:
                self._vel_pub.publish(json.dumps({'x': -50, 'theta': 0}))
            self._target = None
            time.sleep(0.1)


class MotionDetector(object):
    def __init__(self):
        self._motion_pub = jps.Publisher('found_object')
        self._last_gray = None

    def detect_motion(self, img, out_img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        if self._last_gray is None:
            self._last_gray = gray
            return
        frame_diff = cv2.absdiff(self._last_gray, gray)
        _, thresh = cv2.threshold(frame_diff, 50, 255, cv2.THRESH_BINARY)
        thresh = cv2.dilate(thresh, None, iterations=2)
        cnts, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL,
                                   cv2.CHAIN_APPROX_SIMPLE)
        if len(cnts) == 0:
            return
        areas = [cv2.contourArea(c) for c in cnts]
        max_index = -1
        max_area = 0
        for i in range(len(areas)):
            area = areas[i]
            if area > max_area and area > 1000 and area < 5000:
                max_index = i
                max_area = area
        if max_index == -1:
            return
        c = cnts[max_index]
        x, y, w, h = cv2.boundingRect(c)
        cv2.rectangle(out_img, (x, y), (x + w, y + h), (0, 0, 255), 2)
        x_rate, y_rate, area_rate = standardize_by_size(x + w / 2, y + h / 2, h * w, img)
        self._motion_pub.publish(json.dumps({'type': 'motion', 'x': x_rate, 'y': y_rate}))
        self._last_gray = gray


class FaceDetector(object):
    
    def __init__(self):
        self._face_cascade = cv2.CascadeClassifier(
            '/usr/share/opencv/haarcascades/haarcascade_frontalface_default.xml')
        self._face_pub = jps.Publisher('found_object')

    def detect_faces(self, img, out_img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = self._face_cascade.detectMultiScale(gray, 1.3, 5)
        if len(faces) > 0:
            # use first one only for now
            face = faces[0]
            x, y, w, h = face
            cv2.rectangle(out_img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            x_rate, y_rate, area_rate = standardize_by_size(x + w / 2, y + h / 2, h * w, img)
            self._face_pub.publish(json.dumps({
                        'type': 'face',
                        'x': x_rate,
                        'y': y_rate,
                        'area': area_rate,
                        }))
            

class JpsImagePublisher(object):

    def __init__(self, host, jpeg_quality=100):
        self._pub = jps.Publisher('image_processed', host=host)
        self._jpeg_quality = jpeg_quality
        
    def publish(self, image):
        is_success, encoded_image = cv2.imencode(".jpeg", image,
                                                 [int(cv2.IMWRITE_JPEG_QUALITY),
                                                  self._jpeg_quality])
        if is_success:
            self._pub.publish(encoded_image.tostring())
            return True
        else:
            return False


class ImageProcessor(object):
    def __init__(self, callbacks, host='smilerobotics.com'):
        self._image_sub = jps.Subscriber('image', self.image_callback, host=host)
        self._image_pub = JpsImagePublisher(host=host)
        self._callbacks = callbacks

    def image_callback(self, msg):
        jpg_data = np.fromstring(msg, dtype="uint8")
        self._cv_image = cv2.imdecode(jpg_data, 1)
        out_image = self._cv_image.copy()
        for call in self._callbacks:
            call(self._cv_image, out_image)
        self._image_pub.publish(out_image)

    def main(self):
        self._image_sub.spin()

        
def main():
    try:
        color = ColorExtract()
        face = FaceDetector()
        motion = MotionDetector()
        im = ImageProcessor([color.callback, face.detect_faces, motion.detect_motion])
        im.main()
    except KeyboardInterrupt:
        pass

        
if __name__ == '__main__':
    main()


