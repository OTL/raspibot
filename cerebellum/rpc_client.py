#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import socket
import xmlrpclib


class CerebrumRpcClient(object):
    
    def __init__(self, uri='http://smilerobotics.com:12346'):
        self._rpc = xmlrpclib.ServerProxy(uri, allow_none=True)
        self._is_server_available = True

    def get_command(self, sensor_data):
        if not self._is_server_available:
            return {}
        try:
            socket.setdefaulttimeout(0.2)
            command = self._rpc.get_command(sensor_data)
            socket.setdefaulttimeout(None)
            return command
        except socket.error as e:
            self._is_server_available = False
            return {}


if __name__ == '__main__':
    main()
