# -*- coding:utf-8 -*-
import sys
import datetime
import win32evtlog
import winerror

h = win32evtlog.OpenEventLog("localhost", "System")
f = win32evtlog.EVENTLOG_FORWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
# e = win32evtlog.ReadEventLog(h, f, 0)

# [Windowsの起動やスリープなどの履歴を調べてみた！ – A2\-blog]
#   <https://edit-anything.com/blog/windows-power-log.html>
targets = {
    1:    ('S', u'スリープ状態から復帰したとき'),
    12:   ('S', u'OS起動時'),
    13:   ('E', u'OSシャットダウン時'),
    42:   ('E', u'スリープ状態になったとき'),
    6005: ('S', u'起動時'),
    6006: ('E', u'正常にシャットダウン'),
    6008: ('E', u'正常にシャットダウンせずに終了'),
    6009: ('-', u'起動時にブート情報を記録'),
    7001: ('S', u'起動時'),
    7002: ('E', u'正常にシャットダウン'),
}
days_ev = dict()
target_ids = targets.keys()
e = True
ts = datetime.time(0, 0, 0)
te = datetime.time(23, 59, 59)
fb = datetime.datetime.now().strftime('%Y%m%d%H%M%S')

fba = f'A_{fb}.csv'
with open(fba, 'w', encoding="utf_8_sig") as fd:
    while e:
        e = win32evtlog.ReadEventLog(h, f, 0)
        for e_obj in e:
            e_time = e_obj.TimeGenerated
            e_id = winerror.HRESULT_CODE(e_obj.EventID)

            if e_id in target_ids:
                d = e_time.date()
                t = e_time.time()
                days_ev.setdefault(d, {'S': te, 'E': ts})
                if t < days_ev[d]['S']:
                    days_ev[d]['S'] = t
                if t > days_ev[d]['E']:
                    days_ev[d]['E'] = t
                s = '{},{},{},{}\n'.format(d, t, e_id, targets[e_id][1])
                fd.write(s)

fbb = f'B_{fb}.csv'
with open(fbb, 'w', encoding="utf_8_sig") as fd:
    for k in sorted(days_ev.keys()):
        s = '{},{},{}\n'.format(k, days_ev[k]['S'], days_ev[k]['E'])
        fd.write(s)
