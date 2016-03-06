#!/usr/bin/env python

from multiprocessing import Process


def launch_modules(module_names):
    for module_name in module_names:
        m = __import__(module_name)
        p1 = Process(target=m.main)
        p1.start()


def main():
    launch_modules([
        'chibipibot_node',
        'vision_node',
        'mpu_6050_node',
        'battery_node',
        'sound_node',
    ])

    
if __name__ == '__main__':
    main()
