import jps
import json
import time
from chibipibot_driver import ChibiPiBot
from chibipibot_driver import PwmRGB

class ChibiPiBotNode(object):
    
    def __init__(self):
        self._c = ChibiPiBot()
        self._led1 = PwmRGB(19, 16, 26)
        self._led2 = PwmRGB(6, 12, 13)
        self._pub = jps.Publisher('sensor')
        self._sub_vel = jps.Subscriber('cmd_vel', self._vel_callback)
        self._sub_led1 = jps.Subscriber('led1', self._led1_callback)
        self._sub_led2 = jps.Subscriber('led2', self._led2_callback)

    def _vel_callback(self, msg):
        vel = json.loads(msg)
        self._c.set_velocity(vel["x"], vel["theta"])

    def _led1_callback(self, msg):
        led = json.loads(msg)
        self._led1.set_rgb(led.get("r"), led.get("g"), led.get("b"))

    def _led2_callback(self, msg):
        led = json.loads(msg)
        self._led2.set_rgb(led.get("r"), led.get("g"), led.get("b"))
            
    def main(self):
        while True:
            s = self._c.get_sensor_data()
            self._pub.publish(json.dumps(s))
            self._sub_vel.spin_once()
            self._sub_led1.spin_once()
            self._sub_led2.spin_once()
            time.sleep(0.01)

if __name__ == '__main__':
    node = ChibiPiBotNode()
    node.main()
    
