# -*- coding:utf-8 -*-
# import sys
import datetime
import win32evtlog
import winerror
import sqlite3

TargetSourceNames = ('Microsoft-Windows-Kernel-Power',
                     'Microsoft-Windows-Kernel-Boot',
                     'Microsoft-Windows-Winlogon')
TargetIDs = (12, 13, 6005, 6006, 6008)


def isTarget(SourceName, ID):
    if SourceName in TargetSourceNames:
        return True

    if ID in TargetIDs:
        return True

    return False


def Event2DB():
    DBcons = dict()
    h = win32evtlog.OpenEventLog("localhost", "System")
    f = win32evtlog.EVENTLOG_FORWARDS_READ | \
        win32evtlog.EVENTLOG_SEQUENTIAL_READ
    while e := win32evtlog.ReadEventLog(h, f, 0):
        for ee in e:
            eID = winerror.HRESULT_CODE(ee.EventID)
            if isTarget(ee.SourceName, eID):
                # print(ee.TimeGenerated,eID,ee.SourceName)
                dbID = ee.TimeGenerated.strftime('%Y%m')
                if dbID not in DBcons:
                    db = f'pconoff{dbID}.db'
                    con = sqlite3.connect(db)
                    cur = con.cursor()
                    DBcons[dbID] = (con, cur)

                    # Create table
                    cur.execute(
                      'CREATE TABLE if not exists pconoff'
                      ' (gtime timestamp, ID int, SName text,'
                      '  UNIQUE(gtime,ID,SName))')
                else:
                    con, cur = DBcons[dbID]

                # Insert a row of data
                t = ee.TimeGenerated
                s = ee.SourceName
                cur.execute(
                    f"INSERT INTO pconoff VALUES ('{t}',{eID},'{s}')"
                    " on conflict(gtime,ID,SName) do nothing")

    for k in DBcons:
        con, cur = DBcons[k]
        con.commit()
        con.close()


def main():
    Event2DB()

    dv = dict()
    tv = dict()
    ts = datetime.time(0, 0, 0)
    te = datetime.time(23, 59, 59)

    n = datetime.datetime.today()
    m = datetime.datetime(n.year, n.month, 1) - datetime.timedelta(days=1)
    DBs = [m.strftime('%Y%m'), n.strftime('%Y%m')]

    for k in DBs:
        db = f'file:pconoff{k}.db?mode=rw'
        try:
            con = sqlite3.connect(db, uri=True)
        except Exception:
            continue

        cur = con.cursor()
        for row in cur.execute('SELECT * FROM pconoff ORDER BY gtime'):
            tt = datetime.datetime.fromisoformat(row[0])
            d = tt.date()
            t = tt.time()
            dv.setdefault(d, {'S': te, 'E': ts})
            if t < dv[d]['S']:
                dv[d]['S'] = t
            if t > dv[d]['E']:
                dv[d]['E'] = t
        con.close()
        tv.setdefault(k, datetime.timedelta(seconds=0))

    for k in sorted(dv.keys()):
        dte = datetime.datetime.combine(k, dv[k]['E'])
        dts = datetime.datetime.combine(k, dv[k]['S'])
        tt = dte - dts
        s = '{},{},{},{}'.format(k, dv[k]['S'], dv[k]['E'], tt)
        print(s)
        m = dts.strftime('%Y%m')
        tv[m] += tt

    for k in sorted(tv.keys()):
        s = tv[k].total_seconds()
        print(k, '{}h {:02d}m'.format(int(s // 3600), int(s % 3600 // 60)))


if __name__ == '__main__':
    main()
