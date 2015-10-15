#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import socket
import httplib
import time
import threading
import xmlrpclib

class HTTP_with_timeout(httplib.HTTP):
    def __init__(self, host='', port=None, strict=None, timeout=5.0):
        if port == 0: port = None
        self._setup(self._connection_class(host, port, strict, timeout=timeout))

    def getresponse(self, *args, **kw):
        return self._conn.getresponse(*args, **kw)

class TimeoutTransport(xmlrpclib.Transport):
    timeout = 0.5
    def set_timeout(self, timeout):
        self.timeout = timeout
    def make_connection(self, host):
        h = HTTP_with_timeout(host, timeout=self.timeout)
        return h

class CerebrumRpcClient(object):
    
    def __init__(self, uri='http://smilerobotics.com:12346'):
        self._rpc = xmlrpclib.ServerProxy(uri, allow_none=True, transport=TimeoutTransport())
        self._thread = threading.Thread(target=self.call_rpc_loop)
        self._thread.setDaemon(True)
        self._thread.start()
        self._command = {}
        self._sensor_data = {}

    def get_command(self, sensor_data):
        self._sensor_data = sensor_data
        return self._command

    def call_rpc_loop(self):
        while True:
            # TODO: need lock?
            self._command = self.call_rpc()
            time.sleep(0.01)

    def call_rpc(self):
        try:
            socket.setdefaulttimeout(0.5)
#            print('rpc')
#            print(self._sensor_data)
            command = self._rpc.get_command(self._sensor_data)
#            print('rpc end')
            socket.setdefaulttimeout(None)
            return command
        except socket.error as e:
             return {}


if __name__ == '__main__':
    main()
