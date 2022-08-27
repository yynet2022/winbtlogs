# -*- coding:utf-8 -*-
# import sys
import datetime
import win32evtlog
import winerror
# from pprint import pprint

h = win32evtlog.OpenEventLog("localhost", "System")
f = win32evtlog.EVENTLOG_FORWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
# e = win32evtlog.ReadEventLog(h, f, 0)

id2str = {
    12: '[BOOT] OSは (時間) に起動しました',
    13: '[STOP] OSは (時間) にシャットダウンします',
    18: 'このシステムには 0x** ブート オプションがあります',
    20: '前回のブートの成功状態は true/false でした',
    25: 'ブート メニュー ポリシーは 0x** でした',
    26: '今回の起動では 1 回限りのブート シーケンスが使用されました',
    27: '[BOOT] ブートの種類は 0x** でした',
    30: 'ファームウェアからブート メトリックが報告されました',
    32: 'bootmgr はユーザー入力待ちで**秒を費やしました',
    40: 'デバイスによって電源の切り替えが中止されました',
    42: '[STOP] システムがスリープ状態になります',
    107: '[BOOT] システムがスリープ状態から再開されました',
    109: '[STOP] シャットダウンへの切り替えを開始しました',
    130: 'ファームウェア???',
    131: 'ファームウェア???',
    153: '仮想化ベースのセキュリティ ???',
    172: '接続がスタンバイ状態です',
    187: '[STOP] ユーザーはSuspend/Power API でシステム状態の変更を試みました',
    238: 'EFI/ファームウェアの時刻 ???',
    566: 'システム セッションが xx から yy に切り替わりました',
}

days_ev = dict()
e = True
ts = datetime.time(0, 0, 0)
te = datetime.time(23, 59, 59)
fb = datetime.datetime.now().strftime('%Y%m%d%H%M%S')

TargetSourceNames = ('Microsoft-Windows-Kernel-Power',
                     'Microsoft-Windows-Kernel-Boot')
TargetGeneralTypes = (12, 13)


def is_target(SourceName, ID):
    if SourceName in TargetSourceNames:
        return True

    if SourceName == 'Microsoft-Windows-Kernel-General':
        if ID in TargetGeneralTypes:
            return True
    return False


fba = f'A_{fb}.csv'
with open(fba, 'w', encoding='utf_8_sig') as fd:
    while e := win32evtlog.ReadEventLog(h, f, 0):
        for e_obj in e:
            e_id = winerror.HRESULT_CODE(e_obj.EventID)
            if is_target(e_obj.SourceName, e_id):
                e_time = e_obj.TimeGenerated

                d = e_time.date()
                t = e_time.time()
                days_ev.setdefault(d, {'S': te, 'E': ts})
                if t < days_ev[d]['S']:
                    days_ev[d]['S'] = t
                if t > days_ev[d]['E']:
                    days_ev[d]['E'] = t

                try:
                    s = id2str[e_id]
                except Exception:
                    s = '---'

                w = '{},{},{},{}\n'.format(d, t, e_id, s)
                fd.write(w)

fbb = f'B_{fb}.csv'
with open(fbb, 'w', encoding='utf_8_sig') as fd:
    for k in sorted(days_ev.keys()):
        s = '{},{},{}\n'.format(k, days_ev[k]['S'], days_ev[k]['E'])
        fd.write(s)

fbc = f'C_{fb}.csv'
with open(fba, 'r', encoding='utf_8_sig') as fda:
    a = fda.readlines()
    a.sort()
    with open(fbc, 'w', encoding='utf_8_sig') as fdc:
        for b in a:
            fdc.write(b)
