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
        self.main_window = MainWindow(loop_cb=self._loop,
                                      scan_cb=self._scan,
                                      device_data_cb=self._get_device_data)
        self.main_window.get_device_data = self._get_device_data
        self.main_window.initUi()
        self.main_window.dbNewDevices = self._dbagent.get_new_device_count()
        self._scan()
        self._update_devices(True)
        sys.exit(self.app.exec_())

    def command_scanner(self, command):
        self.scanner_queue.put(command)

    def _loop(self):
        readables = list(filter(lambda c: c.poll(), [self.scanner_conn]))
        for readable in readables:
            data = readable.recv()
            if isinstance(data, ScanResult):
                self._dbagent.add_scan_result(data)
                self._update_devices()
                self.main_window.dbNewDevices = self._dbagent.get_new_device_count()
                if self.main_window.deviceWindow.isVisible():
                    self.main_window.deviceWindow.device = self._dbagent.get_device_info(self.main_window.openDeviceId)
        if not self.scanner_queue.empty():
            self.scanner_conn.send(self.scanner_queue.get())

    def _scan(self):
        if self.scanner_queue.empty():
            self.command_scanner(('scan', ('10.100.102.0/24', s.NAME + s.VENDOR)))

    def _update_devices(self, loading=False):
        devices = self._dbagent.get_devices_info()
        if not devices:
            return
        self.main_window.updateDevices(devices, loading)

    def _get_device_data(self, device_id):
        result = self._dbagent.get_device_info(device_id)
        return result

    def _device_scan_clicked(self, ip, mac):
        self.main_window.deviceWindow.deviceLabel.linkActivated.disconnect()
        self._update_device_window(self._dbagent.get_device_info(self.open_device_id), True)
        self.command_scanner(('scan_ports', (ip, mac)))

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
