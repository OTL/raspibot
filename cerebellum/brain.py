import collections

class Sensor(object):
    def get_sensor_data():
        pass


class Cerebellum(object):

    def __init__(self, sensor, command_map, applications):
        self._sensor = sensor
        self._sensor_history = collections.deque([self._sensor.get_sensor_data()], 100)
        self._command = {}
        self._applications = applications
        self._command_drivers = command_map
        self._ignoring_time = {}

    def subscribe_command(self, command_name, func):
        if command_name in self._command_drivers:
            self._command_drivers[command_name].append(func)
        else:
            self._command_drivers[command_name] = [func]

    def add_application(self, app):
        self._applications.append(app)

    def execute(self, command):
        for key, val in command.items():
            try:
                for drv in self._command_drivers[key]:
                    drv(val)
            except KeyError:
                print 'key ' + key + 'not found'

    def get_sensor_data(self):
        return self._sensor.get_sensor_data()

    def get_command(self, sensor_dict):
        command = {}
        history_list = list(self._sensor_history)
        for app in self._applications:
            app(sensor_dict, command, history_list, self._ignoring_time)

        self._sensor_history.append(sensor_dict)
        return command

    def get_sensor_and_execute(self):
        sensor = self.get_sensor_data()
        print sensor
        print sensor['on_flat_ground']
        print sensor['average_rotation']
        command = self.get_command(sensor)
        self.execute(command)
