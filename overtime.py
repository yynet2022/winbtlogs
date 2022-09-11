# -*- coding:utf-8 -*-
# import sys
import datetime

DAY_OFF = 10
AM_OFF = 20
PM_OFF = 30


class _OvertimeCalc:
    WORK_START_TIME = datetime.time(hour=8, minute=30)
    WORK_END_TIME = datetime.time(hour=17, minute=30)
    LUNCH_START_TIME = datetime.time(hour=12, minute=0)
    LUNCH_END_TIME = datetime.time(hour=13, minute=0)

    REST_TIMES = []

    def tostr(t):
        s = t.total_seconds()
        p = ' '
        if s < 0:
            s *= -1
            p = '-'
        return '{}{}h {:02d}m {:02d}s'.format(
            p, int(s // 3600), int(s % 3600 // 60), int(s % 60))

    def calcResttime(self, ts, te):
        t = datetime.timedelta(0)
        d = datetime.datetime.today()

        ls = self.LUNCH_START_TIME if ts < self.LUNCH_START_TIME else ts
        le = self.LUNCH_END_TIME if self.LUNCH_END_TIME < te else te
        if ls < le:
            t += (datetime.datetime.combine(d, le) -
                  datetime.datetime.combine(d, ls))

        for r in self.REST_TIMES:
            ls = r[0] if ts < r[0] else ts
            le = r[1] if r[1] < te else te
            if ls < le:
                t += (datetime.datetime.combine(d, le) -
                      datetime.datetime.combine(d, ls))

        # print('R>', ts, te, t)
        return t

    def calc(self, s_time, e_time, type_off=0, target_date=None):
        if type_off == DAY_OFF:
            return datetime.timedelta(0)

        t_date = target_date
        if t_date is None:
            t_date = datetime.date.today()

        ts = s_time
        if type_off == AM_OFF and ts < self.LUNCH_START_TIME:
            ts = self.LUNCH_START_TIME

        te = e_time
        if type_off == PM_OFF and self.LUNCH_END_TIME < te:
            te = self.LUNCH_END_TIME

        if te <= ts:
            # 例えば、午後休みなのに 14時～15時勤務、とかがここに来る。
            return datetime.timedelta(0)

        wt = datetime.timedelta(0)
        if type_off == AM_OFF:
            wt += (datetime.datetime.combine(t_date, self.WORK_END_TIME) -
                   datetime.datetime.combine(t_date, self.LUNCH_END_TIME))
        elif type_off == PM_OFF:
            wt += (datetime.datetime.combine(t_date, self.LUNCH_START_TIME) -
                   datetime.datetime.combine(t_date, self.WORK_START_TIME))
        else:
            wt += (datetime.datetime.combine(t_date, self.WORK_END_TIME) -
                   datetime.datetime.combine(t_date, self.WORK_START_TIME) -
                   (datetime.datetime.combine(t_date, self.LUNCH_END_TIME) -
                    datetime.datetime.combine(t_date, self.LUNCH_START_TIME)))

        dts = datetime.datetime.combine(t_date, ts)
        dte = datetime.datetime.combine(t_date, te)
        t = dte - dts

        t -= self.calcResttime(ts, te)
        t -= wt

        print('>', s_time, e_time, _OvertimeCalc.tostr(t))
        return t


class MyOvertime(_OvertimeCalc):
    WORK_START_TIME = datetime.time(hour=8, minute=30)
    WORK_END_TIME = datetime.time(hour=17, minute=15)
    LUNCH_START_TIME = datetime.time(hour=12, minute=15)
    LUNCH_END_TIME = datetime.time(hour=13, minute=15)

    REST_TIMES = [(datetime.time(hour=18, minute=30),
                   datetime.time(hour=19, minute=15))]


def main():
    t7 = datetime.time(hour=7, minute=0)
    t12 = datetime.time(hour=12, minute=30)
    t13 = datetime.time(hour=13, minute=0)
    t18 = datetime.time(hour=18, minute=30)

    o = MyOvertime()
    o.calc(t7, t18)
    o.calc(t18, t7)

    print('---')
    o.calc(t7, datetime.time(hour=11, minute=30), PM_OFF)
    o.calc(t7, datetime.time(hour=12, minute=0), PM_OFF)
    o.calc(t7, datetime.time(hour=12, minute=15), PM_OFF)
    o.calc(t7, datetime.time(hour=12, minute=30), PM_OFF)
    o.calc(t7, datetime.time(hour=13, minute=0), PM_OFF)
    o.calc(t7, datetime.time(hour=13, minute=15), PM_OFF)
    o.calc(t7, datetime.time(hour=13, minute=20), PM_OFF)

    print('---')
    o.calc(datetime.time(hour=11, minute=30), t18, AM_OFF)
    o.calc(datetime.time(hour=12, minute=0),  t18, AM_OFF)
    o.calc(datetime.time(hour=12, minute=15), t18, AM_OFF)
    o.calc(datetime.time(hour=12, minute=30), t18, AM_OFF)
    o.calc(datetime.time(hour=13, minute=0),  t18, AM_OFF)
    o.calc(datetime.time(hour=13, minute=15), t18, AM_OFF)
    o.calc(datetime.time(hour=13, minute=20), t18, AM_OFF)


if __name__ == '__main__':
    main()
