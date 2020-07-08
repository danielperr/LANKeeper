# pylint: skip-file
# LANKeeper (https://github.com/danielperr/LANKeeper)
# Manager (main file)

from multiprocessing import Process, Pipe
from queue import Queue
import ctypes
import sys
import time

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

import scan as s
import monitor as m
import history as h
from dbagent import DBAgent
from scanresult import ScanResult
from monitorevent import MonitorEvent
from gui import *


class Manager:

    def __init__(self):
        self._dbagent = DBAgent(new=bool('new' in sys.argv))

        # Scanner
        self.scanner_queue = Queue()
        self.scanner_conn, scanner_side = Pipe()
        self.scanner_process = Process(
            target=s.Scanner,
            args=(scanner_side, ))
        self.scanner_process.daemon = True
        self.scanner_process.start()

        # Monitor
        self.monitor_queue = Queue()
        self.monitor_conn, monitor_side = Pipe()
        self.monitor_process = Process(
            target=m.Monitor,
            args=(monitor_side, )
        )
        self.monitor_process.daemon = True
        self.monitor_process.start()

        self.app = QApplication(sys.argv)
        self.app.setStyle('fusion')
        self.main_window = MainWindow(self)
        self.main_window.get_device_data = self.get_device_data
        self.main_window.initUi()
        self.main_window.dbNewDevices = self._dbagent.get_new_device_count()
        self.scan()
        self._update_devices(True)
        self._update_mgs()
        sys.exit(self.app.exec_())

    def command_scanner(self, command):
        self.scanner_queue.put(command)

    # Callback methods
    def loop(self):
        readables = list(filter(lambda c: c.poll(), [self.scanner_conn, self.monitor_conn]))
        for readable in readables:
            data = readable.recv()
            if isinstance(data, ScanResult):
                self._dbagent.add_scan_result(data)
                self._update_devices()
                self.main_window.dbNewDevices = self._dbagent.get_new_device_count()
                if self.main_window.deviceWindow.isVisible():
                    device = self._dbagent.get_device_info(self.main_window.openDeviceId)
                    if data.detailed:
                        self.main_window.deviceWindow.scanDone()
                    device.monitor_events = self._dbagent.get_monitor_reports(device.ip)
                    self.main_window.deviceWindow.device = device
            elif isinstance(data, MonitorEvent):
                # print('--------------------- manager ok')
                self._dbagent.add_monitor_report(data)
                self._update_devices()
        if not self.scanner_queue.empty():
            self.scanner_conn.send(self.scanner_queue.get())
        if not self.monitor_queue.empty():
            self.monitor_conn.send(self.monitor_queue.get())

    def scan(self):
        if self.scanner_queue.empty():
            self.command_scanner(('scan', ('10.100.102.0/24', s.NAME + s.VENDOR)))

    def scan_ports_os(self, ip):
        self.command_scanner(('scan', (ip, s.PORTS + s.OS)))

    def get_device_data(self, device_id):
        device = self._dbagent.get_device_info(device_id)
        device.monitor_events = self._dbagent.get_monitor_reports(device.ip)
        return device

    def ignore_new_devices(self):
        self._dbagent.ignore_new_devices()
        time.sleep(0.1)
        self._update_devices()
        self.main_window.dbNewDevices = 0

    def update_device_mg(self, device_ip, mg_id):
        self._dbagent.update_device_mg(device_ip, mg_id)
        self._update_mgs()

    def add_mg(self, mg):
        self._dbagent.add_mg(mg)
        self._update_mgs()

    def delete_mgs(self, mg_ids):
        for mgid in mg_ids:
            # Check if the mg has ip addresses and move them to default mg
            ips = self._dbagent.get_mg(mgid=mgid).ips
            for ip in ips:
                self._dbagent.update_device_mg(ip, 1)
            self._dbagent.remove_mg(mgid)
        self._dbagent.reindex_mgs()
        self._update_mgs()

    def update_mg(self, mgid, mg):
        self._dbagent.update_mg(mgid, mg)
        self._update_mgs()

    def _update_devices(self, loading=False):
        devices = self._dbagent.get_devices_info()
        if not devices:
            return
        # check monitor reports
        for device in devices:
            device.monitor_events = self._dbagent.get_monitor_reports(device.ip)
        self.main_window.updateDevicesTable(devices, loading)
        self.main_window.updateDashboard(devices)
        if self.main_window.openDeviceId:
            self.main_window.deviceWindow.device = self.get_device_data(self.main_window.openDeviceId)

    def _update_mgs(self):
        mgs = self._dbagent.get_mgs()
        self.main_window.updateMGtable(mgs)
        self.command_monitor(('update_mgs', (mgs,)))

    def command_monitor(self, cmd):
        self.monitor_queue.put(cmd)

    # def _device_scan_clicked(self, ip, mac):
    #     self.main_window.deviceWindow.deviceLabel.linkActivated.disconnect()
    #     self._update_device_window(self._dbagent.get_device_info(self.open_device_id), True)
    #     self.command_scanner(('scan_ports', (ip, mac)))

    def _device_selected(self, item):
        self.open_device_id = self.main_window.device_ids[item.row()]
        self._update_device_window(self._dbagent.get_device_info(self.open_device_id))
        self.main_window.deviceWindow.show()

    def ignore_traffic(self, ip, action):
        self.command_monitor(('unblock_action', (ip, action)))
        self._dbagent.ignore_action(ip, action)
        self._update_devices()

    def ignore_process(self, ip, process):
        self.command_monitor(('add_process', (ip, process)))
        self._dbagent.ignore_process(ip, process)
        self._update_devices()

    def ignore_drive(self, ip, drive):
        self.command_monitor(('add_drive', (ip, drive)))
        self._dbagent.ignore_drive(ip, drive)
        self._update_devices()

    def ignore_website(self, ip, website):
        self.command_monitor(('ack_website', (ip, website)))
        self._dbagent.ignore_website(ip, website)
        self._update_devices()


def main():
    if is_admin():
        try:
            m = Manager()
        except KeyboardInterrupt:
            print('done.')
    else:
        # NOTE does not print to terminal
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


if __name__ == '__main__':
    main()
