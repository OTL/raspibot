#!/usr/bin/python
# -*- coding: utf-8 -*-

from mpu_6050 import Mpu6050Reader
from mpu_6050 import get_rotation
import jps
import json
import time

def main():
    imu = Mpu6050Reader()
    pub = jps.Publisher('imu', host='smilerobotics.com')
    try:
        while True:
            data = {}
            data['temperature'] = imu.get_temperature()
            angular_vel = imu.get_angular_velocity()
            data['angular_velocity'] = {'x': angular_vel[0], 'y': angular_vel[1], 'z': angular_vel[2],}
            acc = imu.get_acceleration()
            data['acceleration'] = {'x': acc[0], 'y': acc[1], 'z': acc[2]}
            rot = get_rotation(*acc)
            data['rotation'] = {'x': rot[0], 'y': rot[1]}
            pub.publish(json.dumps(data))
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
