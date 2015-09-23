#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import socket
import time
import utils
import xmlrpclib

from chibi import ChibiPiBot


def main():
    bot = ChibiPiBot()
    rpc = xmlrpclib.ServerProxy('http://smilerobotics.com:12346')
    while True:
        time.sleep(0.5)
        try:
            socket.setdefaulttimeout(1)
            command = rpc.get_command(bot.get_sensor_data())
            socket.setdefaulttimeout(None)
            if command['velocity']:
                bot.set_velocity(*command['velocity'])
            if command['speak']:
                utils.speak(command['speak'])
        except socket.error as e:
            print(e)
            bot.set_velocity(0, 0)


if __name__ == '__main__':
    main()
