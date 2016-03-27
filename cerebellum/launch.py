#!/usr/bin/env python

import jps.launcher


def main():
    try:
        jps.launcher.launch_modules([
            'chibipibot_node',
            'vision_node',
            'mpu_6050_node',
            'battery_node',
            'sound_node',
            'event_node',
        ])
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
