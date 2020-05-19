# LANKeeper (https://github.com/danielperr/LANKeeper)
# database agent

"""
NOTIFICATOPM LEVELS
1) info
2) warning
3) critical
"""

from datetime import datetime
import os
import sqlite3

from device import Device
from monitorgroup import MonitorGroup
from detectors.detectors import default_detectors
from monitorevent import MonitorEvent


DB_PATH = os.path.expandvars(r'%APPDATA%\LANKeeper\lankeeper.db')
DATETIME_FORMAT = r'%m/%d/%Y@%H:%M:%S'  # change of this format REQUIRES table drop


class DBAgent:

    def __init__(self, *, new=False, db_path=DB_PATH):
        """
        new (bool): whether to create a fresh db
        db_path (str): database file path
        """
        self.path = db_path
        if new:
            self._drop()
        self._create()
        if new:
            self.add_mg(MonitorGroup(name='Default Group', detectors=default_detectors))

    def _create(self):
        """Create the tables"""
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute('''CREATE TABLE IF NOT EXISTS hosts(
                          id INTEGER PRIMARY KEY NOT NULL,
                          ip TEXT UNIQUE NOT NULL,
                          mac TEXT,
                          name TEXT,
                          vendor TEXT,
                          ports TEXT,
                          os TEXT,
                          first_joined TEXT NOT NULL,
                          last_seen TEXT NOT NULL,
                          mg_id INTEGER NOT NULL,
                          new_device INTEGER NOT NULL)''')
            cur.execute('''CREATE TABLE IF NOT EXISTS monitorgroups(
                          id INTEGER PRIMARY KEY NOT NULL,
                          name TEXT UNIQUE NOT NULL,
                          ips TEXT,
                          detectors TEXT,
                          websites TEXT)''')
            cur.execute('''CREATE TABLE IF NOT EXISTS log(
                          id INTEGER PRIMARY KEY NOT NULL,
                          ip TEXT NOT NULL,
                          time TEXT NOT NULL,
                          type INTEGER NOT NULL,
                          ignore INTEGER NOT NULL,
                          action TEXT,
                          process TEXT,
                          drive TEXT)''')
            conn.commit()

    def _drop(self):
        """Delete all the tables"""
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute('''DROP TABLE IF EXISTS hosts''')
            cur.execute('''DROP TABLE IF EXISTS monitorgroups''')
            cur.execute('''DROP TABLE IF EXISTS log''')
            conn.commit()

    def _connect(self):
        if not os.path.isfile(self.path):
            with open(self.path, 'x'):
                pass
        return sqlite3.connect(self.path)

    # <hosts>
    def add_scan_result(self, scan_result):
        """Update hosts from ScanResult object"""
        strtime = scan_result.time.strftime(DATETIME_FORMAT)
        with self._connect() as conn:
            cur = conn.cursor()
            for host in scan_result.hosts:
                cur.execute('''SELECT id FROM hosts WHERE ip=?''', (host.ip, ))
                dbhost = cur.fetchone()
                if not dbhost:  # new host
                    cur.execute('''INSERT INTO hosts(ip,
                                                     mac,
                                                     name,
                                                     vendor,
                                                     ports,
                                                     os,
                                                     first_joined,
                                                     last_seen,
                                                     mg_id,
                                                     new_device) VALUES(?,?,?,?,?,?,?,?,?,?)''',
                                (host.ip,
                                 host.mac,
                                 host.name,
                                 host.vendor,
                                 '\n'.join(map(str, host.ports)),
                                 host.os,
                                 strtime,
                                 strtime,
                                 1,
                                 1))
                else:
                    cur.execute('''SELECT id,
                                          mac,
                                          name,
                                          vendor,
                                          ports,
                                          os,
                                          last_seen
                                   FROM hosts WHERE ip = ?''',
                                (host.ip, ))
                    result = cur.fetchone()
                    cur.execute('''UPDATE hosts SET mac = ?,
                                                    name = ?,
                                                    vendor = ?,
                                                    ports = ?,
                                                    os = ?,
                                                    last_seen = ?
                                   WHERE id = ?''',
                                (host.mac if host.mac else result[1],
                                 host.name if host.name else result[2],
                                 host.vendor if host.vendor else result[3],
                                 '\n'.join(map(str, host.ports)) if host.ports else result[4],
                                 host.os if host.os else result[5],
                                 strtime if strtime else result[6],
                                 result[0]))
            conn.commit()

    def get_devices_info(self) -> list:
        """Get devices info from hosts for GUI
        :returns: list of Device objects"""
        with self._connect() as conn:
            result = conn.execute('''SELECT id,
                                            ip,
                                            mac,
                                            name,
                                            vendor,
                                            ports,
                                            os,
                                            first_joined,
                                            last_seen,
                                            mg_id,
                                            new_device
                                     FROM hosts''')
            return [Device(id_=int(d[0]),
                           ip=d[1],
                           mac=d[2],
                           name=d[3],
                           vendor=d[4],
                           ports=self._extract_list(d[5]),
                           os=d[6],
                           first_joined=self._extract_datetime(d[7]),
                           last_seen=self._extract_datetime(d[8]),
                           mg_id=int(d[9]),
                           new_device=bool(d[10])) for d in result]

    def get_device_info(self, device_id):
        """Get detailed device info"""
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute('''SELECT id,
                                  ip,
                                  mac,
                                  name,
                                  vendor,
                                  ports,
                                  os,
                                  first_joined,
                                  last_seen,
                                  mg_id,
                                  new_device
                           FROM hosts WHERE id = ?''', (device_id, ))
            conn.execute('''UPDATE hosts SET new_device = ? WHERE id = ?''', (False, device_id))
            result = cur.fetchone()
            conn.commit()
            return Device(id_=int(result[0]),
                          ip=result[1],
                          mac=result[2],
                          name=result[3],
                          vendor=result[4],
                          ports=self._extract_list(result[5]),
                          os=result[6],
                          first_joined=self._extract_datetime(result[7]),
                          last_seen=self._extract_datetime(result[8]),
                          mg_id=int(result[9]),
                          new_device=bool(result[10]))

    def get_new_device_count(self):
        with self._connect() as conn:
            result = conn.execute('''SELECT new_device FROM hosts''')
            return len(list(filter(bool, [x[0] for x in result])))

    def update_device_mg(self, device_id, mg_id):
        with self._connect() as conn:
            conn.execute('''UPDATE hosts
                            SET mg_id = ?
                            WHERE id = ?''', (mg_id, device_id))
    # </hosts>

    # <monitor groups>
    def add_mg(self, mg: MonitorGroup):  # TODO: try-catch this if name already exists
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute('INSERT INTO monitorgroups(name, ips, detectors, websites) VALUES(?,?,?,?)',
                        (mg.name,
                         '\n'.join(sorted(mg.ips)),
                         '\n'.join(sorted(map(str, mg.detectors))),
                         '\n'.join(mg.websites)))
            conn.commit()

    def update_mg(self, mgid, mg: MonitorGroup):
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute('''UPDATE monitorgroups SET name = ?,
                                                    ips = ?,
                                                    detectors = ?,
                                                    websites = ?
                           WHERE id = ?''', (mg.name,
                                             '\n'.join(sorted(mg.ips)),
                                             '\n'.join(sorted(map(str, mg.detectors))),
                                             '\n'.join(mg.websites),
                                             mgid))

    def remove_mg(self, mgid: int):
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute('DELETE FROM monitorgroups WHERE id = ?', (mgid, ))
            conn.commit()

    def get_mgs(self) -> list:
        with self._connect() as conn:
            result = conn.execute('SELECT id, name, ips, detectors, websites FROM monitorgroups')
            return [(x[0], MonitorGroup(name=x[1],
                                        ips=self._extract_list(x[2]),
                                        detectors=list(map(int, self._extract_list(x[3]))),
                                        websites=self._extract_list(x[4])))
                    for x in result]

    def get_mg(self, name: str) -> MonitorGroup:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute('SELECT ips, detectors FROM monitorgroups WHERE name = ?', (name, ))
            result = cur.fetchone()
            conn.commit()
            return MonitorGroup(name, ips=set(result[0].split(',')), detectors=set(result[1].split(',')))
    # </monitor groups>

    # <monitor reports>
    def add_monitor_report(self, need_to_work_this_out):
        """Add activity report from monitor"""
        pass

    def get_monitor_reports(self, ip) -> list:
        """:returns list of the latest MonitorEvent from each type (if exists)"""
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute('''SELECT id,
                                  type,
                                  time,
                                  ignore,
                                  action,
                                  process,
                                  drive
                           FROM log
                           WHERE ip = ?
                           ORDER BY id DESC''', (ip, ))
            results = cur.fetchall()
            types = [False] * 3
            events = []
            for r in results:
                if not types[r[1]]:
                    types[r[1]] = True
                    events.append(MonitorEvent(id_=r[0],
                                               ip=ip,
                                               time=self._extract_datetime(r[2]),
                                               type=r[1],
                                               ignore=bool(r[3]),
                                               action=str(r[4]),
                                               process=str(r[5]),
                                               drive=str(r[6])))
            conn.commit()
            return events

    # </monitor reports>

    def _extract_list(self, input):
        if not input:
            return []
        result = input.split('\n')
        return result if result[0] else []

    def _extract_datetime(self, input):
        return datetime.strptime(input, DATETIME_FORMAT)

    def pretty_date(self, time=False):
        """
        Get a datetime object or a int() Epoch timestamp and return a
        pretty string like 'an hour ago', 'Yesterday', '3 months ago',
        'just now', etc
        """
        now = datetime.now()
        if type(time) is int:
            diff = now - datetime.fromtimestamp(time)
        elif isinstance(time, datetime):
            diff = now - time
        elif not time:
            diff = now - now
        second_diff = diff.seconds
        day_diff = diff.days

        if day_diff < 0:
            return ''

        if day_diff == 0:
            if second_diff < 10:
                return "just now"
            if second_diff < 60:
                return str(int(second_diff)) + " seconds ago"
            if second_diff < 120:
                return "a minute ago"
            if second_diff < 3600:
                return str(int(second_diff / 60)) + " minutes ago"
            if second_diff < 7200:
                return "an hour ago"
            if second_diff < 86400:
                return str(int(second_diff / 3600)) + " hours ago"
        if day_diff == 1:
            return "Yesterday"
        if day_diff < 7:
            return str(int(day_diff)) + " days ago"
        if day_diff < 31:
            return str((int(day_diff / 7))) + " weeks ago"
        if day_diff < 365:
            return str((int(day_diff / 30))) + " months ago"
        return str((int(day_diff / 365))) + " years ago"


if __name__ == "__main__":
    dba = DBAgent()
    devices = dba.get_devices_info()
    print('\n'.join(map(lambda device: ' | '.join(map(str, device)), devices)))
