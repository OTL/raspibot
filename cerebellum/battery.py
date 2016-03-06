from utils import AverageFilter

class BatteryEstimator(object):
    # below table is from
    # https://www.maximintegrated.com/jp/app-notes/index.mvp/id/4189
    V_REMAIN_TABLE = ((4.177, 100.0),
                      (4.026, 82.5),
                      (3.884, 60.0),
                      (3.841, 55.0),
                      (3.793, 40.0),
                      (3.762, 25.0),
                      (3.686, 10.0),
                      (3.674, 5.0),
                      (3.305, 0.0))
    def __init__(self, filter_size=50):
        self._filter = AverageFilter(filter_size)

    def add_voltage(self, v):
        self._filter.append(v)

    def get_percent(self):
        v_ave = self._filter.get_average()
        if v_ave >= self.V_REMAIN_TABLE[0][0]:
            return 100.0
        elif v_ave <= self.V_REMAIN_TABLE[-1][0]:
            return 0.0
        for i, v_p_n in enumerate(self.V_REMAIN_TABLE):
            v_n0 = v_p_n[0]
            p_n0 = v_p_n[1]
            if v_ave < v_n0:
                v_p_n1 = self.V_REMAIN_TABLE[i - 1]
                v_n1 = v_p_n1[0]
                p_n1 = v_p_n1[1]
                return p_n0 + (p_n1 - p_n0) / (v_n1 - v_n0) * (v_ave - v_n0)


def main():
    b = BatteryEstimator(1)
    for i in range(130):
        v = 3.0 + float(i) * 0.01
        b.add_voltage(v)
        print '{} {}'.format(v, b.get_percent())

        
if __name__ == '__main__':
    main()
        
