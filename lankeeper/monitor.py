# LANKeeper (https://github.com/danielperr/LANKeeper)
# Monitor module

import wmi
import time
import sqlite3
import json
import os
import threading as t
from datetime import datetime

from detectors.detectors import detectors
from monitorevent import MonitorEvent


DEFAULT_PATH = os.path.expandvars('%APPDATA%\\LANKeeper\\monitoring.json')
SUSPECT_THRESHOLD = 0.7  # percentage to suspect
ALERT_THRESHOLD = 5  # consecutive times to alert
PROCESS_BLACKLIST = ['WmiApSrv.exe', 'taskeng.exe', 'SearchFilterHost.exe', 'SearchProtocolHost.exe', 'SystemSettings.exe']
TRAINING_PERIOD = 10

# wmi creds
WMI_USER = 'REMOTE'  # these are the same for all wmi supported pcs
WMI_PASS = 'H4dGfcMB6gDk'


class Monitor:

    def __init__(self, manager_conn, **kwargs):
        self._manager_conn = manager_conn
        self.path = DEFAULT_PATH
        self.wmi_supported = self._get_wmi_supported()
        self.detectors = [d() for d in detectors]
        print(self.wmi_supported)
        self.connections = {ip: wmi.WMI(ip, user=WMI_USER, password=WMI_PASS) for ip in self.wmi_supported}
        # if True:
        # training_count = 0
        listen_thread_obj = t.Thread(target=self.listen_thread, args=(self._manager_conn,))
        listen_thread_obj.start()
        self.wmi_routine()

    def listen_thread(self, _manager_conn):
        while True:
            print('bruh')
            command = _manager_conn.recv()
            print('received')
            if command:
                self._run_command(command)

    def _run_command(self, cmd):
        if isinstance(cmd, tuple):  # has args
            print('running command', cmd)
            eval('self.' + cmd[0])(*cmd[1])
        else:
            eval(cmd)()

    # <detectors>
    def traffic_thread(self):
        sniff(filter='ip', prn=self._feed_detectors)

    def traffic_check(self):
        events = []
        for detector in self.detectors:
            ips = detector.detect()
            events += [MonitorEvent(ip=ip,
                                    time=datetime.now(),
                                    type=MonitorEvent.TRAFFIC,
                                    action=detector.name) for ip in ips]
        for event in events:
            self._manager_conn.send(event)

    def _feed_detectors(self, p):
        for detector in self.detectors:
            detector.handle_packet(p)
    # </detectors>

    # <wmi>
    def wmi_routine(self):
        while True:
            for ip in self.wmi_supported:
                info = self.get_info_from_ip(ip)
                processes = info[0]
                processes = [p for p in processes if p not in PROCESS_BLACKLIST]
                # processes = ['System Idle Process', 'System', 'smss.exe', 'csrss.exe', 'wininit.exe', 'csrss.exe', 'services.exe', 'winlogon.exe', 'lsass.exe', 'svchost.exe', 'svchost.exe', 'svchost.exe', 'dwm.exe', 'svchost.exe', 'svchost.exe', 'svchost.exe', 'svchost.exe', 'svchost.exe', 'svchost.exe', 'spoolsv.exe', 'svchost.exe', 'MsMpEng.exe', 'svchost.exe', 'sihost.exe', 'taskhostw.exe', 'explorer.exe', 'SkypeHost.exe', 'RuntimeBroker.exe', 'ShellExperienceHost.exe', 'SearchIndexer.exe', 'igfxtray.exe', 'hkcmd.exe', 'igfxpers.exe', 'OneDrive.exe', 'svchost.exe', 'InstallAgent.exe', 'MpCmdRun.exe', 'dllhost.exe', 'msdtc.exe', 'ApplicationFrameHost.exe', 'SystemSettings.exe', 'LockAppHost.exe', 'LockApp.exe', 'SearchUI.exe', 'GoogleCrashHandler.exe', 'GoogleCrashHandler64.exe', 'WmiPrvSE.exe', 'igfxsrvc.exe', 'dllhost.exe', 'dllhost.exe', 'Taskmgr.exe']
                # check if something has been rarely / never opened
                # if not suspicious, record
                # if suspicious, start recording in a different column
                #   if a couple of recordings afterwards it becomes normal again, add to normal records
                #   if not, alert!
                self._db_add_record(ip, processes, True)
                suspiciousness = self.check_suspiciousness(ip)
                print(suspiciousness)
                if suspiciousness[1] > SUSPECT_THRESHOLD:
                    if self._db_check_stash_total(ip) > ALERT_THRESHOLD:
                        print('[!!!] Suspicious traffic for ip %s' % ip)
                        self._manager_conn.send(MonitorEvent(ip=ip,
                                                             time=datetime.now(),
                                                             type=MonitorEvent.PROCESS,
                                                             process=suspiciousness[0]))
                else:
                    self._db_move_to_final(ip)
                # training_count += 1
                time.sleep(1)
                drives = info[1]
                new_drive = self.check_drives(ip, drives)
                if new_drive:
                    print('[!!!] Suspicious drive for ip %s' % ip)
                    self._manager_conn.send(MonitorEvent(ip=ip,
                                                         time=datetime.now(),
                                                         type=MonitorEvent.DRIVE,
                                                         drive=new_drive))

    def get_info_from_ip(self, ip):
        """returns (processes, drives)"""
        print(f'trying to connect WMI to ip {ip}')
        conn = self.connections[ip]
        return ([p.caption for p in conn.Win32_Process()],
                [d.volumename for d in conn.Win32_LogicalDisk(DriveType=2) if d.volumename])

    def check_suspiciousness(self, ip):
        """:returns: (process, suspiciousness_amount)"""
        with open(self.path) as f:
            data = json.load(f)
        deviations = dict()
        final_total = data[ip]['total']['final']
        stash_total = data[ip]['total']['stash']
        if final_total:
            for p, v in data[ip]['processes'].items():
                if 'stash' not in v:
                    continue
                final = v.get('final', 0)
                stash = v.get('stash', 0)
                deviations[p] = ((abs(final / final_total - stash / stash_total))**2)
        else:
            return '', 0
        # print('\n'.join(['%s : %s' % (p, v) for p, v in deviations.items() if v > 0.0]))
        if not deviations:
            return '', 0
        max_process = max(deviations, key=deviations.get)
        return max_process, deviations[max_process]

    def check_drives(self, ip, drives) -> str:
        """:returns: suspicious drive name (if exists)
        if not returns empty str"""
        with open(self.path) as f:
            data = json.load(f)
        data[ip].setdefault('drives', [])
        known = data[ip]['drives']
        new_drive = ''
        for drive in drives:
            if drive not in known:
                print(f'{drive=} {known=}')
                new_drive = drive
        with open(self.path, 'w') as f:
            json.dump(data, f)
        return new_drive

    def add_drive(self, ip, drive):
        with open(self.path) as f:
            data = json.load(f)
        data[ip].setdefault('drives', [])
        data[ip]['drives'].append(drive)
        with open(self.path, 'w') as f:
            json.dump(data, f)

    def add_process(self, ip, process):
        with open(self.path) as f:
            data = json.load(f)
        data[ip]['processes'][process] = data[ip]['total'].copy()
        with open(self.path, 'w') as f:
            json.dump(data, f)

    def _db_check_stash_total(self, ip):
        with open(self.path) as f:
            data = json.load(f)
        return data[ip]['total']['stash']

    def _db_add_record(self, ip, processes, stash=False):
        self._check_file()
        processes = list(set(processes))
        with open(self.path) as f:
            data = json.load(f)
        if ip not in data:
            data[ip] = dict()
        if 'total' not in data[ip]:
            data[ip]['total'] = dict()
            data[ip]['total']['final'] = 0
            data[ip]['total']['stash'] = 0
        key = 'stash' if stash else 'final'
        data[ip]['total'][key] += 1
        if 'processes' not in data[ip]:
            data[ip]['processes'] = dict()
        for p in processes:
            if p not in data[ip]['processes']:
                data[ip]['processes'][p] = dict()
            if key not in data[ip]['processes'][p]:
                data[ip]['processes'][p][key] = 0
            data[ip]['processes'][p][key] += 1
        with open(self.path, 'w') as f:
            json.dump(data, f)

    def _db_move_to_final(self, ip):
        with open(self.path) as f:
            data = json.load(f)
        data[ip]['total']['final'] += data[ip]['total']['stash']
        data[ip]['total']['stash'] = 0
        for p in data[ip]['processes'].keys():
            if 'final' not in data[ip]['processes'][p]:
                data[ip]['processes'][p]['final'] = 0
            if 'stash' in data[ip]['processes'][p]:
                data[ip]['processes'][p]['final'] += data[ip]['processes'][p]['stash']
                data[ip]['processes'][p].pop('stash', None)
        with open(self.path, 'w') as f:
            json.dump(data, f)

    def _check_file(self):
        if not os.path.isfile(self.path):
            with open(self.path, 'x') as f:
                json.dump({}, f)
        return open(self.path, 'r+')

    def _get_wmi_supported(self):
        with open(os.path.expandvars('%APPDATA%\\LANKeeper\\wmi_supported.txt')) as f:
            return [ip.strip() for ip in f.readlines()]
    # </wmi>


if __name__ == '__main__':
    try:
        mon = Monitor('10.100.102.55')
    except KeyboardInterrupt:
        pass
