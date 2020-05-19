# pylint: skip-file
# LANKeeper (https://github.com/danielperr/LANKeeper)
# Manager (main file)

from multiprocessing import Process, Pipe
from queue import Queue
import ctypes
import sys

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

import scan as s
import history as h
from dbagent import DBAgent
from scanresult import ScanResult
from gui import *


class Manager:

    def __init__(self):
        self._dbagent = DBAgent(new=bool('new' in sys.argv))

        self.scanner_queue = Queue()
        self.scanner_conn, scanner_side = Pipe()
        self.scanner_process = Process(
            target=s.Scanner,
            args=(scanner_side, ))
        self.scanner_process.daemon = True
        self.scanner_process.start()

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
        readables = list(filter(lambda c: c.poll(), [self.scanner_conn]))
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
                    self.main_window.deviceWindow.device = device
        if not self.scanner_queue.empty():
            self.scanner_conn.send(self.scanner_queue.get())

    def scan(self):
        if self.scanner_queue.empty():
            self.command_scanner(('scan', ('10.100.102.0/24', s.NAME + s.VENDOR)))

    def scan_ports_os(self, ip):
        self.command_scanner(('scan', (ip, s.PORTS + s.OS)))

    def get_device_data(self, device_id):
        result = self._dbagent.get_device_info(device_id)
        return result

    def update_device_mg(self, device_id, mg_id):
        self._dbagent.update_device_mg(device_id, mg_id)

    def add_mg(self, mg):
        self._dbagent.add_mg(mg)
        self._update_mgs()

    def delete_mgs(self, mg_ids):
        for mgid in mg_ids:
            self._dbagent.remove_mg(mgid)
        self._update_mgs()

    def update_mg(self, mgid, mg):
        self._dbagent.update_mg(mgid, mg)
        self._update_mgs()

    # Private methods
    def _update_devices(self, loading=False):
        devices = self._dbagent.get_devices_info()
        if not devices:
            return
        self.main_window.updateDevicesTable(devices, loading)

    def _update_mgs(self):
        mgs = self._dbagent.get_mgs()
        self.main_window.updateMGtable(mgs)

    # def _device_scan_clicked(self, ip, mac):
    #     self.main_window.deviceWindow.deviceLabel.linkActivated.disconnect()
    #     self._update_device_window(self._dbagent.get_device_info(self.open_device_id), True)
    #     self.command_scanner(('scan_ports', (ip, mac)))

    def _device_selected(self, item):
        self.open_device_id = self.main_window.device_ids[item.row()]
        self._update_device_window(self._dbagent.get_device_info(self.open_device_id))
        self.main_window.deviceWindow.show()


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
