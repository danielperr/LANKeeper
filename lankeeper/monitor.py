# maybe truncate records that are too old? new programs will take forever to sink in the model

import wmi
import time
import sqlite3
import json
import os

DEFAULT_PATH = os.path.expandvars('%APPDATA%\\LANKeeper\\monitoring.json')
SUSPECT_THRESHOLD = 0.7  # percentage to suspect
ALERT_THRESHOLD = 5  # consecutive times to alert
PROCESS_BLACKLIST = ['WmiApSrv.exe', 'taskeng.exe', 'SearchFilterHost.exe', 'SearchProtocolHost.exe', 'SystemSettings.exe']
TRAINING_PERIOD = 10


class Monitor:

    def __init__(self, ip):
        self.path = DEFAULT_PATH
        # if True:
        # training_count = 0
        while True:
            processes = [p for p in self.get_processes_from_ip(ip) if p not in PROCESS_BLACKLIST]
            # processes = ['System Idle Process', 'System', 'smss.exe', 'csrss.exe', 'wininit.exe', 'csrss.exe', 'services.exe', 'winlogon.exe', 'lsass.exe', 'svchost.exe', 'svchost.exe', 'svchost.exe', 'dwm.exe', 'svchost.exe', 'svchost.exe', 'svchost.exe', 'svchost.exe', 'svchost.exe', 'svchost.exe', 'spoolsv.exe', 'svchost.exe', 'MsMpEng.exe', 'svchost.exe', 'sihost.exe', 'taskhostw.exe', 'explorer.exe', 'SkypeHost.exe', 'RuntimeBroker.exe', 'ShellExperienceHost.exe', 'SearchIndexer.exe', 'igfxtray.exe', 'hkcmd.exe', 'igfxpers.exe', 'OneDrive.exe', 'svchost.exe', 'InstallAgent.exe', 'MpCmdRun.exe', 'dllhost.exe', 'msdtc.exe', 'ApplicationFrameHost.exe', 'SystemSettings.exe', 'LockAppHost.exe', 'LockApp.exe', 'SearchUI.exe', 'GoogleCrashHandler.exe', 'GoogleCrashHandler64.exe', 'WmiPrvSE.exe', 'igfxsrvc.exe', 'dllhost.exe', 'dllhost.exe', 'Taskmgr.exe']
            # check if something has been rarely / never opened
            # if not suspicious, record
            # if suspicious, start recording in a different column
            #   if a couple of recordings afterwards it becomes normal again, add to normal records
            #   if not, alert!
            self._db_add_record(ip, processes, True)
            if self.check_suspiciousness(ip) > SUSPECT_THRESHOLD:
                if self._db_check_stash_total(ip) > ALERT_THRESHOLD:
                    print('[!!!] Suspicious activity for ip %s' % ip)
            else:
                self._db_move_to_final(ip)
            # training_count += 1
            time.sleep(1)

    def get_processes_from_ip(self, ip):
        conn = wmi.WMI(ip, user='DESKTOP-I2TJ1T1\\SHAY', password='3177')
        return [p.caption for p in conn.Win32_Process()]

    def check_suspiciousness(self, ip):
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
            return 0
        print('\n'.join(['%s : %s' % (p, v) for p, v in deviations.items() if v > 0.0]))
        return max(deviations.values())

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


if __name__ == '__main__':
    try:
        mon = Monitor('10.100.102.55')
    except KeyboardInterrupt:
        pass
