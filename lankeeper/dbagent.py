# LANKeeper (https://github.com/danielperr/LANKeeper)
# database agent

"""
TABLE LIST
* hosts
* reports
* analysis
* notifications

NOTIFICATOPM LEVELS
1) info
2) warning
3) critical
"""

from datetime import datetime
import os
import sqlite3


DB_PATH = os.path.expandvars(r'%APPDATA%\LANKeeper\lankeeper.db')
DATETIME_FORMAT = r'%m/%d/%Y@%H:%M:%S'  # change of this format REQUIRES table drop


class DBAgent:

    def __init__(self, **kwargs):
        """
        :keyword args:
            * new (bool): whether to create a fresh db
        """
        self.path = kwargs.get('db_path', DB_PATH)
        new = kwargs.get('new', False)
        if new:
            self._drop()
        self._create()

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
            conn.commit()

    def _drop(self):
        """Delete all the tables"""
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute('''DROP TABLE IF EXISTS hosts''')
            conn.commit()

    def _connect(self):
        if not os.path.isfile(self.path):
            with open(self.path, 'x'):
                pass
        return sqlite3.connect(self.path)

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
                                (host.ip, host.mac, host.name, host.vendor, ','.join(map(str, host.ports)), strtime, strtime, True))
                else:
                    cur.execute('''SELECT id, mac, name, vendor, last_seen, ports FROM hosts WHERE ip = ?''', (host.ip, ))
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

    def add_monitor_report(self, need_to_work_this_out):
        """Add activity report from monitor"""
        pass

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
            result = conn.execute('''SELECT name,
                                            ip,
                                            mac,
                                            vendor,
                                            first_joined,
                                            last_seen,
                                            ports FROM hosts WHERE id = %s''' % device_id)
            conn.execute('''UPDATE hosts SET new_device = ? WHERE id = ?''', (False, device_id))
            return list(result)[0]

    def get_new_device_count(self):
        with self._connect() as conn:
            result = conn.execute('''SELECT new_device FROM hosts''')
            return len(list(filter(bool, [x[0] for x in result])))
    
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
