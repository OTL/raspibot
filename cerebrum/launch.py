#!/usr/bin/env python

import jps

def main():
    try:
        jps.launcher.launch_modules(['jps.forwarder', 'websocket_server', 'vision_node', 'http_server'])
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    main()

