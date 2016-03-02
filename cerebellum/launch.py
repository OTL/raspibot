#!/usr/bin/env python

import chibipibot_node
import vision_node
import mpu_6050_node

from multiprocessing import Process

def main():
    p1 = Process(target=chibipibot_node.main)
    p1.start()
    p2 = Process(target=vision_node.main)
    p2.start()
    p3 = Process(target=mpu_6050_node.main)
    p3.start()

    
if __name__ == '__main__':
    main()
    
        
    
