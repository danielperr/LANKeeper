# LANKeeper (https://github.com/danielperr/LANKeeper)
# database agent

"""
NOTIFICATOPM LEVELS
1) info
2) warning
3) critical
"""

from device import Device
from monitorgroup import MonitorGroup
from detectors.detectors import default_detectors

from datetime import datetime
import os
import sqlite3


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
                          vendor TEXT,
                          name TEXT,
                          ports TEXT,
                          first_joined TEXT NOT NULL,
                          last_seen TEXT NOT NULL,
                          new_device BOOL)''')
            cur.execute('''CREATE TABLE IF NOT EXISTS monitorgroups(
                          id INTEGER PRIMARY KEY NOT NULL,
                          name TEXT UNIQUE NOT NULL,
                          ips TEXT,
                          detectors TEXT)''')
            conn.commit()

    def _drop(self):
        """Delete all the tables"""
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute('''DROP TABLE IF EXISTS hosts''')
            cur.execute('''DROP TABLE IF EXISTS monitorgroups''')
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
                    cur.execute('''INSERT INTO hosts(
                        ip, mac, name, vendor, ports, first_joined, last_seen, new_device) VALUES(?,?,?,?,?,?,?,?)''',
                                (host.ip, host.mac, host.name, host.vendor,
                                 ','.join(map(str, host.ports)), strtime, strtime, True))
                else:
                    cur.execute('''SELECT id, mac, name, vendor, last_seen, ports FROM hosts WHERE ip = ?''',
                                (host.ip, ))
                    result = cur.fetchone()
                    cur.execute('''UPDATE hosts SET last_seen = ?,
                                                   mac = ?,
                                                   name = ?,
                                                   vendor = ?,
                                                   ports = ?
                                WHERE id = ?''',
                                (strtime if strtime else result[4],
                                 host.mac if host.mac else result[1],
                                 host.name if host.name else result[2],
                                 host.vendor if host.vendor else result[3],
                                 ','.join(map(str, host.ports)) if host.ports else result[5],
                                 result[0]))
            conn.commit()

    def get_devices_info(self):
        """Get devices info from hosts for GUI
        :returns: id_list, data_list"""
        with self._connect() as conn:
            result = conn.execute('SELECT id, new_device, ip, name, vendor, last_seen FROM hosts')
            return [(x[0],
                     int(x[1]),
                     x[3] if x[3] else x[2],
                     x[4],
                     self.pretty_date(datetime.strptime(x[5], DATETIME_FORMAT)))
                    for x in result]

    def get_device_info(self, device_id):
        """Get detailed device info"""
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute('''SELECT name,
                                  ip,
                                  mac,
                                  vendor,
                                  first_joined,
                                  last_seen,
                                  ports FROM hosts WHERE id = %s''' % device_id)
            conn.execute('''UPDATE hosts SET new_device = ? WHERE id = ?''', (False, device_id))
            result = cur.fetchone()
            conn.commit()
            ports = list(map(int, result[6].split(','))) if result[6] else []
            return Device(ip=result[1],
                          mac=result[2],
                          name=result[0],
                          vendor=result[3],
                          ports=ports,
                          first_joined=datetime.strptime(result[4], DATETIME_FORMAT),
                          last_seen=datetime.strptime(result[5], DATETIME_FORMAT))

    def get_new_device_count(self):
        with self._connect() as conn:
            result = conn.execute('''SELECT new_device FROM hosts''')
            return len(list(filter(bool, [x[0] for x in result])))
    # </hosts>

    # <monitor groups>
    def add_mg(self, mg: MonitorGroup):  # TODO: try-catch this if name already exists
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute('INSERT INTO monitorgroups(name, ips, detectors) VALUES(?,?,?)',
                        (mg.name, ','.join(sorted(mg.ips)), ','.join(sorted(map(str, mg.detectors)))))
            conn.commit()

    def remove_mg(self, name: str):
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute('DELETE FROM monitorgroups WHERE name = ?', (name, ))
            conn.commit()

    def get_mg(self, name: str) -> MonitorGroup:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute('SELECT ips, detectors FROM monitorgroups WHERE name = ?', (name, ))
            result = cur.fetchone()
            conn.execute()
            return MonitorGroup(name, ips=set(result[0].split(',')), detectors=set(result[1].split(',')))
    # </monitor groups>

    def add_monitor_report(self, need_to_work_this_out):
        """Add activity report from monitor"""
        pass

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
