#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import socket
import xmlrpclib


class CerebrumRpcClient(object):
    
    def __init__(self, uri='http://smilerobotics.com:12346')
        self._rpc = xmlrpclib.ServerProxy(uri)

    def get_command(self, sensor_data):
        try:
            socket.setdefaulttimeout(1)
            command = self._rpc.get_command(sensor_data)
            socket.setdefaulttimeout(None)
            return command
        except socket.error as e:
            print(e)
            return {}


if __name__ == '__main__':
    main()
