# -*- coding:utf-8 -*-
# import sys
# import pprint
import datetime
from dataclasses import dataclass

DAY_OFF = 10
AM_OFF  = 20
PM_OFF  = 30

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


def _TM(s):
    h, m = s.split(':')
    return datetime.time(hour=int(h), minute=int(m))


def _DT(s, d):
    h, m = s.split(':')
    t = datetime.time(hour=int(h), minute=int(m))
    return datetime.datetime.combine(d, t)

def _TD(s):
    h, m = s.split(':')
    return datetime.timedelta(hours=int(h), minutes=int(m))


def _TD2str(t):
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
    WORK_TIMES  = (_TM('08:30'), _TM('17:30'))
    LUNCH_TIMES = (_TM('12:00'), _TM('13:00'))

    BASE_TIME  = _TM('05:00')

    REST_TIMES = []

    def isHoliday(self, d):
        return d.weekday() == 5 or d.weekday() == 6

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

        # target date.
        if s_time is None:
            td = datetime.date.today()
        elif s_time.time() < self.BASE_TIME:
            td = s_time.date() - _TD('24:00')
        else:
            td = s_time.date()

        comb = datetime.datetime.combine
        rests = [
            (comb(td, self.LUNCH_TIMES[0]), comb(td, self.LUNCH_TIMES[1]))
        ]
        for r in self.REST_TIMES:
            r0 = comb(td, r[0]) if r[0] >= self.BASE_TIME \
                else comb(td + _TD('24:00'), r[0])
            r1 = comb(td, r[1]) if r[1] >= self.BASE_TIME \
                else comb(td + _TD('24:00'), r[1])

            assert r0 < r1
            rests.append((r0, r1))

        def calc_rest(ts, te, rs):
            t = datetime.timedelta(0)
            for r in rs:
                s = r[0] if ts < r[0] else ts
                e = r[1] if r[1] < te else te
                if s < e:
                    t += e - s

            # print('R>', ts, te, t)
            return t

        def calc_form():
            ts = comb(td, self.WORK_TIMES[0])
            te = comb(td, self.WORK_TIMES[1])
            assert ts < te
            return (te - ts) - calc_rest(ts, te, rests)

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
            ts = comb (td, self.WORK_TIMES[0])
            te = comb (td, self.LUNCH_TIMES[0])
            assert ts < te
            t_paid = (te - ts) - calc_rest(ts, te, rests)
            t_work += t_paid

        elif type_off == PM_OFF:
            ts = comb (td, self.LUNCH_TIMES[1])
            te = comb (td, self.WORK_TIMES[1])
            assert ts < te
            t_paid = (te - ts) - calc_rest(ts, te, rests)
            t_work += t_paid

        # 年休時間と実労働時間が重ならないように調整。
        assert s_time is not None
        ts = s_time
        if type_off == AM_OFF and ts.time() < self.LUNCH_TIMES[0]:
            # 午前休み＆昼休み前に開始しているなら、開始時間を修正
            # それ以外（例えば午後遅くに開始とか）ならば修正しない。
            ts = comb(td, self.LUNCH_TIMES[0])

        assert e_time is not None
        te = e_time
        if type_off == PM_OFF and self.LUNCH_TIMES[1] < te.time():
            # 午後休み＆昼休み後に終了しているなら、終了時間を修正
            # それ以外（例えば午前中に終了とか）ならば修正しない。
            te = comb(td, self.LUNCH_TIMES[1])

        if te <= ts:
            # 例えば、午後休みなのに 14時～15時勤務、とかがここに来る。
            return Worktime(t_form, t_work, t_actl, t_paid, t_rest)

        # 休憩時間（中断時間含む）
        t_rest = calc_rest(ts, te, rests)

        # 実労働時間
        t_actl = (te - ts) - t_rest

        # 勤務時間
        t_work += t_actl

        # print('>', s_time, e_time, _TD2str(t))
        # print('>', s_time, e_time, '|', t_work, t_actl, t_work-t_form)
        return Worktime(t_form, t_work, t_actl, t_paid, t_rest)


class MyOvertime(_OvertimeCalculator):
    WORK_TIMES  = (_TM('08:30'), _TM('17:15'))
    LUNCH_TIMES = (_TM('12:15'), _TM('13:15'))

    REST_TIMES = [
        (_TM('05:00'), _TM('05:30')),
        (_TM('19:15'), _TM('19:45')),
        (_TM('23:15'), _TM('00:00')),
    ]


def main():
    o = MyOvertime()
    d = datetime.date(year=2022, month=9, day=12)

    assert o.calc(type_off=DAY_OFF) == \
        Worktime(form=_TD('07:45'), work=_TD('07:45'),
                 actl=_TD('00:00'), paid=_TD('07:45'), rest=_TD('00:00'))

    assert o.calc(_DT('07:30', d), _DT('18:30', d)) == \
        Worktime(form=_TD('07:45'), work=_TD('10:00'),
                 actl=_TD('10:00'), paid=_TD('00:00'), rest=_TD('01:00'))

    assert o.calc(_DT('08:15', d), _DT('18:30', d)) == \
        Worktime(form=_TD('07:45'), work=_TD('09:15'),
                 actl=_TD('09:15'), paid=_TD('00:00'), rest=_TD('01:00'))

    assert o.calc(_DT('09:00', d), _DT('18:30', d)) == \
        Worktime(form=_TD('07:45'), work=_TD('08:30'),
                 actl=_TD('08:30'), paid=_TD('00:00'), rest=_TD('01:00'))

    assert o.calc(_DT('09:00', d), _DT('19:00', d)) == \
        Worktime(form=_TD('07:45'), work=_TD('09:00'),
                 actl=_TD('09:00'), paid=_TD('00:00'), rest=_TD('01:00'))

    assert o.calc(_DT('09:00', d), _DT('20:30', d)) == \
        Worktime(form=_TD('07:45'), work=_TD('10:00'),
                 actl=_TD('10:00'), paid=_TD('00:00'), rest=_TD('01:30'))

    assert o.calc(_DT('09:00', d), _DT('13:00', d), type_off=PM_OFF) == \
        Worktime(form=_TD('07:45'), work=_TD('07:15'),
                 actl=_TD('03:15'), paid=_TD('04:00'), rest=_TD('00:45'))

    assert o.calc(_DT('12:30', d), _DT('16:00', d), type_off=AM_OFF) == \
        Worktime(form=_TD('07:45'), work=_TD('06:30'),
                 actl=_TD('02:45'), paid=_TD('03:45'), rest=_TD('00:45'))

    def HT(s):
        hd = datetime.date(year=2022, month=9, day=10)
        h, m = s.split(':')
        t = datetime.time(hour=int(h), minute=int(m))
        return datetime.datetime.combine(hd, t)

    assert o.calc(HT('07:10'), HT('13:30')) == \
        Worktime(form=_TD('00:00'), work=_TD('06:20'),
                 actl=_TD('06:20'), paid=_TD('00:00'), rest=_TD('00:00'))

    assert o.calc(HT('12:30'), HT('16:00')) == \
        Worktime(form=_TD('00:00'), work=_TD('03:30'),
                 actl=_TD('03:30'), paid=_TD('00:00'), rest=_TD('00:00'))


if __name__ == '__main__':
    main()
