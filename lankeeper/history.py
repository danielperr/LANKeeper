# LANKeeper (https://github.com/danielperr/LANKeeper)
# History class

from scapy.all import *
import sqlite3 as lite
import threading
import datetime
import time
import os
import re


DB_PATH = '.\\history.db'

DOMAIN = 0
PROCESS = 1


class History (object):

    def __init__(self, db_path=DB_PATH, **kwargs):
        self.db_path = db_path
        if 'new' in kwargs and kwargs['new']:
            self._drop_tables()
        self._create_tables()

    def handle_packet(self, p):
        # p.show()
        if not p.haslayer('DNS'):
            return

        # if p.haslayer('IP'):
        #     conn = self._connect_to_db()
        #     cr = conn.cursor()
        #     cr.execute('''SELECT id FROM hosts WHERE ip=?''', (p['IP'].src, ))
        #     results = cr.fetchone()
        #     if not results:
        #         cr.execute('''INSERT INTO hosts(ip) VALUES(?)''', (p['IP'].src, ))
        #     cr.execute('''SELECT id FROM hosts WHERE ip=?''', (p['IP'].src, ))
        #     results = cr.fetchone()
        #     host_id = results[0]
        #     conn.commit()
        #     conn.close()
        # currently only domain type
        if p.haslayer('DNS'):
            try:  # TODO: check if reply and only then
                self.add_record(p['IP'].src, DOMAIN, p['DNS'].qd[0].qname.decode('ASCII'), datetime.datetime.now())
            except TypeError:
                pass

    def check_tasks(self, ip_list):
        for ip in ip_list:
            wmic_output = os.popen('wmic /node:%s process' % ip).read()
            print('fetched running processes')
            processes = re.findall(r'\n{2}(\S+)', wmic_output)
            for process in processes:
                self.add_record(ip, PROCESS, process, datetime.datetime.now())

    def add_record(self, host_ip, clf, description, time):
        """
        :param host_ip: ip of relevant host
        :param clf: record classification (domain / process)
        :param description: domain / process name
        :param time: datetime object of record time
        """
        conn = self._connect_to_db()
        cr = conn.cursor()
        cr.execute('''INSERT INTO history(host, type, desc, time) VALUES(?,?,?,?)''',
                   (host_ip, clf, description, time.strftime("%m/%d/%Y %H:%M:%S")))
        conn.commit()
        conn.close()

    def _create_tables(self):
        conn = self._connect_to_db()
        cr = conn.cursor()
        cr.execute('''CREATE TABLE IF NOT EXISTS history(
                          id INTEGER PRIMARY KEY NOT NULL,
                          host TEXT NOT NULL,
                          type INTEGER NOT NULL,
                          desc TEXT NOT NULL,
                          time TEXT NOT NULL)''')
        cr.execute('''CREATE TABLE IF NOT EXISTS hosts(
                          id INTEGER PRIMARY KEY NOT NULL,
                          ip TEXT UNIQUE NOT NULL)''')
        conn.commit()
        conn.close()

    def _drop_tables(self):
        conn = self._connect_to_db()
        cr = conn.cursor()
        cr.execute('''DROP TABLE IF EXISTS history''')
        cr.execute('''DROP TABLE IF EXISTS hosts''')
        conn.commit()
        conn.close()

    def _connect_to_db(self):
        """:return: lite.connect object
        DONT FORGET TO CLOSE CONNECTION"""
        conn = None
        if not os.path.isfile(self.db_path):
            with open(self.db_path, 'x'):
                pass
        try:
            conn = lite.connect(self.db_path)
        except lite.Error:
            raise IOError("couldn't open history database")
        return conn


def bgsniff():
    sniff(filter='ip', prn=hs.handle_packet)


if __name__ == '__main__':
    hs = History(new=1)
    t = threading.Thread(target=bgsniff, args=())
    t.start()
    while True:
        hs.check_tasks(['172.16.10.186'])
        time.sleep(60)
