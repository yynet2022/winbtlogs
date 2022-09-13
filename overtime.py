# -*- coding:utf-8 -*-
# import sys
import datetime
from dataclasses import dataclass

DAY_OFF = 10
AM_OFF = 20
PM_OFF = 30

'''
ここでは
・勤務時間＝実労働時間＋年休時間
・勤務時間＝所定労働時間＋残業時間
・所定労働時間＝（所定終了時間－所定開始時間）－所定休憩時間
・所定休憩時間＝昼休み＋その他の予め決められている休憩時間（REST_TIMES）
・年休時間＝終日年休 or 半日年休 or 時間休暇
・半日休暇＋時間休暇は計算上OK
・年休時間は定時にのみ使用可
・実労働時間と年休時間が被っている場合は年休時間を優先
とする。
'''


def _Timedelta2str(t):
    s = t.total_seconds()
    p = ' '
    if s < 0:
        s *= -1
        p = '-'
    return '{}{}:{:02d}:{:02d}'.format(
        p, int(s // 3600), int(s % 3600 // 60), int(s % 60))


@dataclass
class Worktime:
    form: datetime.timedelta
    work: datetime.timedelta
    actl: datetime.timedelta
    paid: datetime.timedelta
    rest: datetime.timedelta

    def __str__(self):
        return 'Wt(form={},work={},actl={},paid={},rest={})'. \
            format(_Timedelta2str(self.form),
                   _Timedelta2str(self.work),
                   _Timedelta2str(self.actl),
                   _Timedelta2str(self.paid),
                   _Timedelta2str(self.rest))


class _OvertimeCalculator:
    WORK_START_TIME = datetime.time(hour=8, minute=30)
    WORK_END_TIME = datetime.time(hour=17, minute=30)
    LUNCH_START_TIME = datetime.time(hour=12, minute=0)
    LUNCH_END_TIME = datetime.time(hour=13, minute=0)

    REST_TIMES = []

    def isHoliday(cls, d):
        return d.weekday() == 5 or d.weekday() == 6

    def calcResttime(self, ts, te):
        ''' 時刻tsから時刻teの間の所定休憩時間 '''
        t = datetime.timedelta(0)
        d = datetime.date.today()

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

    def calc(self, s_time=None, e_time=None, type_off=0):
        if s_time is not None and self.isHoliday(s_time):
            return self.calcHoliday(s_time, e_time)
        else:
            return self.calcWorkday(s_time, e_time, type_off)

    def calcHoliday(self, s_time=None, e_time=None):
        t_form = datetime.timedelta(0)
        t_paid = datetime.timedelta(0)
        t_rest = datetime.timedelta(0)

        t_actl = e_time - s_time if s_time < e_time else datetime.timedelta(0)
        t_work = t_actl

        return Worktime(t_form, t_work, t_actl, t_paid, t_rest)

    def calcWorkday(self, s_time=None, e_time=None, type_off=0):
        '''
        t_form: 所定労働時間
        t_work: 勤務時間
        t_actl: 実労働時間
        t_paid: 有休休暇時間
        t_rest: 休憩時間（中断時間含む）
        '''

        if s_time is None:
            td = datetime.date.today()
        else:
            td = s_time.date()

        def t_intr(s, e):
            if s < e:
                return (datetime.datetime.combine(td, e) -
                        datetime.datetime.combine(td, s))
            else:
                return datetime.timedelta(0)

        def calc_form():
            ts = self.WORK_START_TIME
            te = self.WORK_END_TIME
            tr = self.calcResttime(ts, te)
            return t_intr(ts, te) - tr

        t_form = calc_form()
        t_work = datetime.timedelta(0)
        t_actl = datetime.timedelta(0)
        t_paid = datetime.timedelta(0)
        t_rest = datetime.timedelta(0)

        # 年休時間
        if type_off == DAY_OFF:
            t_work = t_form
            t_paid = t_form
            return Worktime(t_form, t_work, t_actl, t_paid, t_rest)

        elif type_off == AM_OFF:
            ts = self.WORK_START_TIME
            te = self.LUNCH_START_TIME
            tr = self.calcResttime(ts, te)
            t_paid = t_intr(ts, te) - tr
            t_work += t_paid

        elif type_off == PM_OFF:
            ts = self.LUNCH_END_TIME
            te = self.WORK_END_TIME
            tr = self.calcResttime(ts, te)
            t_paid = t_intr(ts, te) - tr
            t_work += t_paid

        # 年休時間と実労働時間が重ならないように調整。
        ts = s_time.time()
        if type_off == AM_OFF and ts < self.LUNCH_START_TIME:
            # 午前休み＆昼休み前に開始しているなら、開始時間を修正
            # それ以外（例えば午後遅くに開始とか）ならば修正しない。
            ts = self.LUNCH_START_TIME

        te = e_time.time()
        if type_off == PM_OFF and self.LUNCH_END_TIME < te:
            # 午後休み＆昼休み後に終了しているなら、終了時間を修正
            # それ以外（例えば午前中に終了とか）ならば修正しない。
            te = self.LUNCH_END_TIME

        if te <= ts:
            # 例えば、午後休みなのに 14時～15時勤務、とかがここに来る。
            return Worktime(t_form, t_work, t_actl, t_paid, t_rest)

        # 休憩時間（中断時間含む）
        t_rest = self.calcResttime(ts, te)

        # 実労働時間
        t_actl = t_intr(ts, te) - t_rest

        # 勤務時間
        t_work += t_actl

        # print('>', s_time, e_time, _Timedelta2str(t))
        # print('>', s_time, e_time, '|', t_work, t_actl, t_work-t_form)
        return Worktime(t_form, t_work, t_actl, t_paid, t_rest)


class MyOvertime(_OvertimeCalculator):
    WORK_START_TIME = datetime.time(hour=8, minute=30)
    WORK_END_TIME = datetime.time(hour=17, minute=15)
    LUNCH_START_TIME = datetime.time(hour=12, minute=15)
    LUNCH_END_TIME = datetime.time(hour=13, minute=15)

    REST_TIMES = [(datetime.time(hour=18, minute=30),
                   datetime.time(hour=19, minute=15))]


def main():
    o = MyOvertime()
    d = datetime.date(year=2022, month=9, day=12)

    def T(s):
        h, m = s.split(':')
        t = datetime.time(hour=int(h), minute=int(m))
        return datetime.datetime.combine(d, t)

    def DT(s):
        h, m = s.split(':')
        return datetime.timedelta(hours=int(h), minutes=int(m))

    assert o.calc(type_off=DAY_OFF) == \
        Worktime(form=DT('7:45'), work=DT('7:45'),
                 actl=DT('00:00'), paid=DT('7:45'), rest=DT('00:00'))

    assert o.calc(T('7:30'), T('18:30')) == \
        Worktime(form=DT('7:45'), work=DT('10:00'),
                 actl=DT('10:00'), paid=DT('00:00'), rest=DT('1:00'))

    assert o.calc(T('8:15'), T('18:30')) == \
        Worktime(form=DT('7:45'), work=DT('9:15'),
                 actl=DT('9:15'), paid=DT('00:00'), rest=DT('1:00'))

    assert o.calc(T('9:00'), T('18:30')) == \
        Worktime(form=DT('7:45'), work=DT('8:30'), actl=DT('8:30'),
                 paid=DT('00:00'), rest=DT('1:00'))

    assert o.calc(T('9:00'), T('19:00')) == \
        Worktime(form=DT('7:45'), work=DT('8:30'),
                 actl=DT('8:30'), paid=DT('00:00'), rest=DT('1:30'))

    assert o.calc(T('9:00'), T('19:30')) == \
        Worktime(form=DT('7:45'), work=DT('8:45'),
                 actl=DT('8:45'), paid=DT('00:00'), rest=DT('1:45'))

    assert o.calc(T('9:00'), T('13:00'), type_off=PM_OFF) == \
        Worktime(form=DT('7:45'), work=DT('7:15'),
                 actl=DT('3:15'), paid=DT('4:00'), rest=DT('0:45'))

    assert o.calc(T('12:30'), T('16:00'), type_off=AM_OFF) == \
        Worktime(form=DT('7:45'), work=DT('6:30'),
                 actl=DT('2:45'), paid=DT('3:45'), rest=DT('0:45'))

    def HT(s):
        hd = datetime.date(year=2022, month=9, day=10)
        h, m = s.split(':')
        t = datetime.time(hour=int(h), minute=int(m))
        return datetime.datetime.combine(hd, t)

    assert o.calc(HT('7:10'), HT('13:30')) == \
        Worktime(form=DT('0:00'), work=DT('6:20'),
                 actl=DT('6:20'), paid=DT('0:00'), rest=DT('0:00'))

    assert o.calc(HT('12:30'), HT('16:00')) == \
        Worktime(form=DT('0:00'), work=DT('3:30'),
                 actl=DT('3:30'), paid=DT('0:00'), rest=DT('0:00'))


if __name__ == '__main__':
    main()
