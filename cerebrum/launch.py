#!/usr/bin/env python

import jps

jps.launcher.launch_modules(['jps.forwarder', 'websocket_server', 'vision_node', 'http_server'])
