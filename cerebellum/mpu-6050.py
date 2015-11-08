#!/usr/bin/python
# -*- coding: utf-8 -*-

# from
# https://gist.githubusercontent.com/wide-snow/1149b0b29064fc1208fa/raw/c425da2ab02f7cbdad4b393c79e0a1d948274d0f/mpu-6050_2.py

import smbus
import math
import time


class Mpu6050Reader(object):
    DEV_ADDR = 0x68
    ACCEL_XOUT = 0x3b
    ACCEL_YOUT = 0x3d
    ACCEL_ZOUT = 0x3f
    TEMP_OUT = 0x41
    GYRO_XOUT = 0x43
    GYRO_YOUT = 0x45
    GYRO_ZOUT = 0x47
    PWR_MGMT_1 = 0x6b
    PWR_MGMT_2 = 0x6c

    def __init__(self, wake_up=True):
        self._bus = smbus.SMBus(1)
        if wake_up:
            self.wake_up()

    def wake_up(self):
        self._bus.write_byte_data(self.DEV_ADDR, self.PWR_MGMT_1, 0)

    def _read_byte(self, adr):
        return self._bus.read_byte_data(self.DEV_ADDR, adr)

    def _read_word(self, adr):
        high = self._read_byte(adr)
        low = self._read_byte(adr + 1)
        val = (high << 8) + low
        return val

    def _read_word_sensor(self, adr):
        val = self._read_word(adr)
        if (val >= 0x8000):
            return -((65535 - val) + 1)
        else:
            return val

    def get_temperature(self):
        temp = self._read_word_sensor(self.TEMP_OUT)
        x = temp / 340 + 36.53
        return x

#
# Angular Velocity: full scale range ±250 deg/s
#        LSB sensitivity 131 LSB/deg/s
#        -> ±250 x 131 = ±32750 LSB[16bit]
#   Gyroscope Configuration GYRO_CONFIG (reg=0x1B)
#   full scale range/LSB sensitivity can be set by FS_SEL(Bit4-Bit3)
#
    def get_gyro_data_lsb(self):
        x = self._read_word_sensor(self.GYRO_XOUT)
        y = self._read_word_sensor(self.GYRO_YOUT)
        z = self._read_word_sensor(self.GYRO_ZOUT)
        return (x, y, z)

    def get_gyro_data_deg(self):
        return tuple([x / 131.0 for x in self.get_gyro_data_lsb()])

#
# Acceleration: full scale range ±2g
#        LSB sensitivity 16384 LSB/g)
#        -> ±2 x 16384 = ±32768 LSB[16bit]
#   Accelerometer Configuration ACCEL_CONFIG (reg=0x1C)
#   full scale range/LSB sensitivity can be set by AFS_SEL(Bit4-Bit3)
#
    def get_accel_data_lsb(self):
        x = self._read_word_sensor(self.ACCEL_XOUT)
        y = self._read_word_sensor(self.ACCEL_YOUT)
        z = self._read_word_sensor(self.ACCEL_ZOUT)
        return (x, y, z)

    def get_accel_data_g(self):
        return tuple([x / 16384.0 for x in self.get_accel_data_lsb()])


def dist(a, b):
    return math.sqrt((a * a) + (b * b))


def get_rotation(acc_x, acc_y, acc_z):
    return (math.atan2(acc_y, dist(acc_x, acc_z)), -math.atan2(acc_x, dist(acc_y, acc_z)))


def main():
    # 温度.
    imu = Mpu6050Reader()
    try:
        while True:
            print 'temperature[C]: %04.1f ||' % imu.get_temperature(),
            print 'gyro[deg/s] x: %08.3f y: %08.3f z: %08.3f' % imu.get_gyro_data_deg(),
            print 'accel[g] x: %06.3f y: %06.3f z: %06.3f' % imu.get_accel_data_g(),
            print 'rotation[rad] x: %06.3f y: %06.3f' % get_rotation(*imu.get_accel_data_g())
            time.sleep(0.1)
    except KeyboardInterrupt as e:
        print e


if __name__ == '__main__':
    main()
