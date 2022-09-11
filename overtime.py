# -*- coding:utf-8 -*-
# import sys
import datetime

DAY_OFF = 10
AM_OFF = 20
PM_OFF = 30

'''
ここでは
・勤務時間＝実労働時間＋年休時間
・勤務時間＝所定労働時間＋残業時間
・実労働時間と年休時間が被っている場合は年休時間でカウント
・年休時間は定時にのみ使用可
とする。
'''


def _Timedelta2str(t):
    s = t.total_seconds()
    p = ' '
    if s < 0:
        s *= -1
        p = '-'
    return '{}{}h {:02d}m {:02d}s'.format(
        p, int(s // 3600), int(s % 3600 // 60), int(s % 60))


class _OvertimeCalculator:
    WORK_START_TIME = datetime.time(hour=8, minute=30)
    WORK_END_TIME = datetime.time(hour=17, minute=30)
    LUNCH_START_TIME = datetime.time(hour=12, minute=0)
    LUNCH_END_TIME = datetime.time(hour=13, minute=0)

    REST_TIMES = []

    def calcResttime(self, ts, te):
        t = datetime.timedelta(0)
        d = datetime.datetime.today()

        def _calc(rs, re):
            nonlocal t
            s = rs if ts < rs else ts
            e = re if re < te else te
            if s < e:
                t += (datetime.datetime.combine(d, e) -
                      datetime.datetime.combine(d, s))
            
        _calc(self.LUNCH_START_TIME, self.LUNCH_END_TIME)
        for r in self.REST_TIMES:
            _calc(r[0], r[1])

        # print('R>', ts, te, t)
        return t

    def calc(self, s_time, e_time, type_off=0, target_date=None):
        if type_off == DAY_OFF:
            return datetime.timedelta(0)

        t_date = target_date
        if t_date is None:
            t_date = datetime.date.today()

        # 年休時間と実労働時間が重ならないように調整。
        ts = s_time
        if type_off == AM_OFF and ts < self.LUNCH_START_TIME:
            ts = self.LUNCH_START_TIME

        te = e_time
        if type_off == PM_OFF and self.LUNCH_END_TIME < te:
            te = self.LUNCH_END_TIME

        if te <= ts:
            # 例えば、午後休みなのに 14時～15時勤務、とかがここに来る。
            return datetime.timedelta(0)

        # 所定労働時間（年休時間省く）を算出
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

        # 実労働時間を算出
        dts = datetime.datetime.combine(t_date, ts)
        dte = datetime.datetime.combine(t_date, te)
        t = dte - dts

        # 休憩時間・中断時間を考慮
        t -= self.calcResttime(ts, te)

        # 所定労働時間（年休時間省く）を引いて残業時間を算出
        t -= wt

        print('>', s_time, e_time, _Timedelta2str(t))
        return t


class MyOvertime(_OvertimeCalculator):
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
