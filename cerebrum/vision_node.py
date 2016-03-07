#!/usr/bin/env python

import json
import time

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
        moments = cv2.moments(mask_image)
        m00 = moments['m00']
        centroid_x, centroid_y = None, None
        if m00 != 0:
            centroid_x = int(moments['m10'] / m00)
            centroid_y = int(moments['m01'] / m00)
        extracted_image = cv2.bitwise_and(cv_image, cv_image, mask=mask_image)
        area = cv2.countNonZero(mask_image)
        return (area, (centroid_x, centroid_y), extracted_image)
        
    def callback(self, cv_image):
        image_width, image_height, _ = cv_image.shape
        center_x = image_width / 2
        center_y = image_height / 2
        red_area, red_centroid, red_image = self.get_colored_area(
            cv_image, np.array([150,100,50]), np.array([180,255,255]))
        if red_area > 100:
            x_rate, y_rate, area_rate = standardize_by_size(red_centroid[0], red_centroid[1], red_area, cv_image)
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

class FaceDetector(object):
    
    def __init__(self):
        self._face_cascade = cv2.CascadeClassifier(
            '/usr/share/opencv/haarcascades/haarcascade_frontalface_default.xml')
        self._face_pub = jps.Publisher('found_object')

    def detect_faces(self, img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = self._face_cascade.detectMultiScale(gray, 1.3, 5)
        if len(faces) > 0:
            # use first one only for now
            face = faces[0]
            x_rate, y_rate, area_rate = standardize_by_size(face[0], face[1], face[2] * face[3], img)
            self._face_pub.publish(json.dumps({
                        'type': 'face',
                        'x': x_rate,
                        'y': y_rate,
                        'area': area_rate,
                        }))


class ImageProcessor(object):
    def __init__(self, callbacks):
        self._image_sub = jps.Subscriber('image', self.image_callback, host='smilerobotics.com')
        self._callbacks = callbacks

    def image_callback(self, msg):
        jpg_data = np.fromstring(msg, dtype="uint8")
        cv_image = cv2.imdecode(jpg_data, 1)
        for call in self._callbacks:
            call(cv_image)

    def main(self):
        self._image_sub.spin()

        
def main():
    color = ColorExtract()
    face = FaceDetector()
    im = ImageProcessor([color.callback, face.detect_faces])
    im.main()
        
if __name__ == '__main__':
    main()


