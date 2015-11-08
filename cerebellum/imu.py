import math

class ImuReader(object):
    def get_accelaration(self):
        pass

    def get_angular_velocity(self):
        pass


def dist(a, b):
    return math.sqrt((a * a) + (b * b))


def get_rotation(acc_x, acc_y, acc_z):
    return (math.atan2(acc_y, dist(acc_x, acc_z)), -math.atan2(acc_x, dist(acc_y, acc_z)))
