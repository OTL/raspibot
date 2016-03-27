from battery import BatteryEstimator
import jps
import json


def main(host='smilerobotics.com'):
    try:
        pub = jps.Publisher('battery', host=host)
        sub = jps.Subscriber('sensor', host=host)
        b = BatteryEstimator(100)
        for msg in sub:
            sensor = json.loads(msg)
            v = sensor['v_battery']
            b.add_voltage(v)
            p = b.get_percent()
            is_charging = False
            if sensor['v_charge'] > 3.0:
                is_charging = True
                pub.publish(json.dumps({'voltage': round(v, 3), 'percent': round(p, 1), 'is_charging': is_charging}))
    except KeyboardInterrupt:
        pass
        
if __name__ == '__main__':
    main(host='smilerobotics.com')
