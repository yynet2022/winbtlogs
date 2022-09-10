# -*- coding:utf-8 -*-
# import sys
import datetime
import win32evtlog
import winerror
import sqlite3

TABLE_NAME = 'pconoff'
DB_NAME = f'{TABLE_NAME}_{{}}.db'
CSV_NAME = f'{TABLE_NAME}_{{}}.csv'

TARGET_SOURCE_NAMES = ('Microsoft-Windows-Kernel-Power',
                       'Microsoft-Windows-Kernel-Boot',
                       'Microsoft-Windows-Winlogon')
TARGET_IDS = (12, 13, 6005, 6006, 6008)


def isTarget(SourceName, ID):
    if SourceName in TARGET_SOURCE_NAMES:
        return True

    if ID in TARGET_IDS:
        return True

    return False


def Event2DB():
    DBcons = dict()
    h = win32evtlog.OpenEventLog('localhost', 'System')
    f = win32evtlog.EVENTLOG_FORWARDS_READ | \
        win32evtlog.EVENTLOG_SEQUENTIAL_READ
    while e := win32evtlog.ReadEventLog(h, f, 0):
        for ee in e:
            eID = winerror.HRESULT_CODE(ee.EventID)
            if isTarget(ee.SourceName, eID):
                dbID = ee.TimeGenerated.strftime('%Y%m')
                if dbID not in DBcons:
                    db = DB_NAME.format(dbID)
                    con = sqlite3.connect(db)
                    cur = con.cursor()
                    DBcons[dbID] = (con, cur)

                    # Create table
                    cur.execute(
                      f'CREATE TABLE if not exists {TABLE_NAME}'
                      ' (gtime timestamp, ID int, SName text,'
                      '  UNIQUE(gtime,ID,SName))')
                else:
                    con, cur = DBcons[dbID]

                # Insert a row of data
                t = ee.TimeGenerated
                s = ee.SourceName
                cur.execute(
                    f"INSERT INTO {TABLE_NAME} VALUES ('{t}',{eID},'{s}')"
                    ' on conflict(gtime,ID,SName) do nothing')

    for k in DBcons:
        con, cur = DBcons[k]
        con.commit()
        con.close()


def main():
    Event2DB()

    tv = dict()
    ts = datetime.time(0, 0, 0)
    te = datetime.time(23, 59, 59)

    n = datetime.datetime.today()
    m = datetime.datetime(n.year, n.month, 1) - datetime.timedelta(days=1)
    DBs = [m.strftime('%Y%m'), n.strftime('%Y%m')]

    for q in DBs:
        _db = DB_NAME.format(q)
        db = f'file:{_db}?mode=rw'
        try:
            con = sqlite3.connect(db, uri=True)
        except Exception:
            continue
        cur = con.cursor()

        dv = dict()
        for row in cur.execute(f'SELECT * FROM {TABLE_NAME} ORDER BY gtime'):
            tt = datetime.datetime.fromisoformat(row[0])
            d = tt.date()
            t = tt.time()
            dv.setdefault(d, {'S': te, 'E': ts})
            if t < dv[d]['S']:
                dv[d]['S'] = t
            if t > dv[d]['E']:
                dv[d]['E'] = t
        con.close()

        tx = datetime.timedelta(seconds=0)
        c = CSV_NAME.format(q)
        with open(c, 'w', encoding='utf_8_sig') as fd:
            for k in sorted(dv.keys()):
                dte = datetime.datetime.combine(k, dv[k]['E'])
                dts = datetime.datetime.combine(k, dv[k]['S'])
                tt = dte - dts
                s = '{},{},{},{}\n'.format(k, dv[k]['S'], dv[k]['E'], tt)
                fd.write(s)
                tx += tt
            ss = tx.total_seconds()
            sss = '{}:{:02d}:{:02d}'.format(
                int(ss // 3600), int(ss % 3600 // 60), int(ss % 60))
            fd.write(f'Total,,,{sss}\n')
            tv[q] = tx

    for k in sorted(tv.keys()):
        ss = tv[k].total_seconds()
        sss = '{}h {:02d}m {:02d}s'.format(
            int(ss // 3600), int(ss % 3600 // 60), int(ss % 60))
        print(k, sss)


if __name__ == '__main__':
    main()
