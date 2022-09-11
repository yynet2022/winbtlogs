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
        '''
        t_work: 勤務時間
        t_actl: 実労働時間
        t_paid: 有休休暇時間
        t_rest: 休憩時間（中断時間含む）
        t_form: 所定労働時間
        '''

        td = target_date
        if td is None:
            td = datetime.date.today()

        def t_intr(s, e):
            if s < e:
                return (datetime.datetime.combine(td, e) -
                        datetime.datetime.combine(td, s))
            else:
                return datetime.timedelta(0)

        ts = self.WORK_START_TIME
        te = self.WORK_END_TIME
        tr = self.calcResttime(ts, te)
        t_form = t_intr(ts, te) - tr

        if type_off == DAY_OFF:
            t_work = t_form
            t_actl = datetime.timedelta(0)
            t_paid = t_form
            t_rest = tr
            return t_actl

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

        # 年休時間
        t_paid = datetime.timedelta(0)
        if type_off == AM_OFF:
            t_paid = t_intr(self.WORK_START_TIME, self.LUNCH_START_TIME)
        elif type_off == PM_OFF:
            t_paid = t_intr(self.LUNCH_END_TIME, self.WORK_END_TIME)

        # 休憩時間（中断時間含む）
        t_rest = self.calcResttime(ts, te)

        # 実労働時間
        t_actl = t_intr(ts, te) - t_rest

        # 勤務時間
        t_work = t_actl + t_paid

        # print('>', s_time, e_time, _Timedelta2str(t))
        print('>', s_time, e_time, '|', t_work, t_actl, t_work-t_form)
        return t_work


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
