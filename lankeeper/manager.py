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
        self._dbagent = DBAgent()

        self.scanner_queue = Queue()
        self.scanner_conn, scanner_side = Pipe()
        self.scanner_process = Process(
            target=s.Scanner,
            args=(scanner_side, ))
        self.scanner_process.daemon = True
        self.scanner_process.start()
        # self.command_scanner(('progressive_scan', ('10.100.102.0/24', s.NAME + s.VENDOR)))

        self.app = QApplication(sys.argv)
        self.main_window = MainWindow(self.loop)
        self._update_devices()
        sys.exit(self.app.exec_())

    def loop(self):
        readables = list(filter(lambda c: c.poll(), [self.scanner_conn]))
        for readable in readables:
            data = readable.recv()
            if isinstance(data, ScanResult):
                self._dbagent.add_scan_result(data)
                self._update_devices()
        if not self.scanner_queue.empty():
            self.scanner_conn.send(self.scanner_queue.get())

    def _update_devices(self):
        devices = self._dbagent.get_devices_info()
        self.main_window.devicesTable.setRowCount(0)
        for row, device in enumerate(devices):
            self.main_window.devicesTable.insertRow(row)
            for col, item in enumerate(device):
                self.main_window.devicesTable.setItem(row, col, QTableWidgetItem(str(item)))

    def command_scanner(self, command):
        self.scanner_queue.put(command)


def main():
    if is_admin():
        try:
            m = Manager()
        except KeyboardInterrupt:
            print('done.')
    else:
        # ! Does not print to terminal !
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


if __name__ == '__main__':
    main()
