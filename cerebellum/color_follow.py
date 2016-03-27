#!/usr/bin/env python

import json
import jps
import cv2
import numpy as np


class ColorExtract(object):
    def __init__(self, host='smilerobotics.com'):
        self._vel_pub = jps.Publisher('cmd_vel', host=host)
        self._image_sub = jps.Subscriber('image', self.callback, host=host)

    def main(self):
        self._image_sub.spin()

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
        
    def callback(self, msg):
        jpg_data = np.fromstring(msg, dtype = "uint8")
        cv_image = cv2.imdecode(jpg_data, 1)
        image_width, image_height, _ = cv_image.shape
        center_x = image_width / 2
        center_y = image_height / 2
        red_area, red_centroid, red_image = self.get_colored_area(
            cv_image, np.array([150,100,50]), np.array([180,255,255]))
        if red_area > 100:
            extracted_rate_x = float(red_centroid[0] - center_x) / image_width
            extracted_rate_y = float(red_centroid[1] - center_y) / image_height
            print('({x}, {y}: area={area}'.format(x=extracted_rate_x, y=extracted_rate_y, area=red_area))
            if extracted_rate_x < -0.4:
                self._vel_pub.publish(json.dumps({'x': 0, 'theta': 50}))
            elif extracted_rate_x < -0.2:
                self._vel_pub.publish(json.dumps({'x': 0, 'theta': 30}))
            elif extracted_rate_x > 0.4:
                self._vel_pub.publish(json.dumps({'x': 0, 'theta': -50}))
            elif extracted_rate_x > 0.2:
                self._vel_pub.publish(json.dumps({'x': 0, 'theta': -30}))
            elif red_area < 1000:
                self._vel_pub.publish(json.dumps({'x': 50, 'theta': 0}))
            elif red_area > 3000:
                self._vel_pub.publish(json.dumps({'x': -50, 'theta': 0}))


def main():
    try:
        color = ColorExtract()
        color.main()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
