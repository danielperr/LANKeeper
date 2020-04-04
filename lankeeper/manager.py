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
        self._dbagent = DBAgent(new=0)

        self.scanner_queue = Queue()
        self.scanner_conn, scanner_side = Pipe()
        self.scanner_process = Process(
            target=s.Scanner,
            args=(scanner_side, ))
        self.scanner_process.daemon = True
        self.scanner_process.start()

        self.app = QApplication(sys.argv)
        self.main_window = MainWindow(self.loop, self.scan)
        self.main_window.deviceSelected = self._device_selected
        self.main_window.initUi()
        self.main_window.dbNewDevices = self._dbagent.get_new_device_count()
        self.scan()
        self._update_devices(True)
        sys.exit(self.app.exec_())

    def loop(self):
        readables = list(filter(lambda c: c.poll(), [self.scanner_conn]))
        for readable in readables:
            data = readable.recv()
            if isinstance(data, ScanResult):
                self._dbagent.add_scan_result(data)
                self._update_devices()
                self.main_window.dbNewDevices = self._dbagent.get_new_device_count()
                if self.main_window.deviceWindow.isVisible():
                    self._update_device_window(self._dbagent.get_device_info(self.open_device_id))
        if not self.scanner_queue.empty():
            self.scanner_conn.send(self.scanner_queue.get())

    def scan(self):
        if self.scanner_queue.empty():
            self.command_scanner(('scan', ('10.100.102.0/24', s.NAME + s.VENDOR)))

    def _update_devices(self, loading=False):
        devices = self._dbagent.get_devices_info()
        if not devices:
            return
        self.main_window.device_ids = list(zip(*devices))[0]
        self.main_window.devicesTable.setRowCount(0)
        for row, device in enumerate([x[1:] for x in devices]):
            self.main_window.devicesTable.insertRow(row)
            for col, item in enumerate(device):
                if col == len(device) - 1 and loading:
                    self.main_window.devicesTable.setItem(row, col, QTableWidgetItem('scanning...'))
                elif col == 0:
                    if item == 1:
                        pixmap = QPixmap(SRC_INFO)
                        pixmap = pixmap.scaled(25, 25, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        label = QLabel()
                        label.setPixmap(pixmap)
                        self.main_window.devicesTable.setCellWidget(row, col, label)
                else:
                    self.main_window.devicesTable.setItem(row, col, QTableWidgetItem(str(item)))

    def _device_selected(self, item):
        self.open_device_id = self.main_window.device_ids[item.row()]
        self._update_device_window(self._dbagent.get_device_info(self.open_device_id))
        self.main_window.deviceWindow.show()

    def _update_device_window(self, data, scan_clicked=False):
        ports = ''
        if scan_clicked:
            if data[-1]:
                ports = data[-1] + ' '
            ports += '<label>(scanning...)</label>'
        elif data[-1]:
            ports = data[-1] + ' <a href="scan">(scan again)</a>'
        else:
            ports = '<a href="scan">(scan ports)</a>'
        self.main_window.deviceWindow.deviceLabel.setText(
            '''<html>
                 <head>
                 </head>
                 <body>
                   <b>Name:</b> %s<br />
                   <b>IP address:</b> %s<br />
                   <b>MAC address:</b> %s<br />
                   <b>NIC vendor:</b> %s<br />
                   <b>First joined:</b> %s<br />
                   <b>Last detected:</b> %s<br />
                   <b>Open ports:</b> %s<br />
                 </body>
               </html>''' % (*data[:-1], ports))
        self.main_window.deviceWindow.deviceLabel.linkActivated.connect(lambda _: 0)
        self.main_window.deviceWindow.deviceLabel.linkActivated.disconnect()
        if not scan_clicked:
            self.main_window.deviceWindow.deviceLabel.linkActivated.connect(lambda _:
                                                                            self._device_scan_clicked(data[1], data[2]))

    def _device_scan_clicked(self, ip, mac):
        self.main_window.deviceWindow.deviceLabel.linkActivated.disconnect()
        self._update_device_window(self._dbagent.get_device_info(self.open_device_id), True)
        self.command_scanner(('scan_ports', (ip, mac)))

    def _device_selected(self, item):
        self.open_device_id = self.main_window.device_ids[item.row()]
        self._update_device_window(self._dbagent.get_device_info(self.open_device_id))
        self.main_window.deviceWindow.show()

    def _update_device_window(self, data, scan_clicked=False):
        ports = ''
        if scan_clicked:
            if data[-1]:
                ports = data[-1] + ' '
            ports += '<label>(scanning...)</label>'
        elif data[-1]:
            ports = data[-1] + ' <a href="scan">(scan again)</a>'
        else:
            ports = '<a href="scan">(scan ports)</a>'
        self.main_window.deviceWindow.deviceLabel.setText(
            '''<html>
                 <head>
                 </head>
                 <body>
                   <b>Name:</b> %s<br />
                   <b>IP address:</b> %s<br />
                   <b>MAC address:</b> %s<br />
                   <b>NIC vendor:</b> %s<br />
                   <b>First joined:</b> %s<br />
                   <b>Last detected:</b> %s<br />
                   <b>Open ports:</b> %s<br />
                 </body>
               </html>''' % (*data[:-1], ports))
        self.main_window.deviceWindow.deviceLabel.linkActivated.connect(lambda _: 0)
        self.main_window.deviceWindow.deviceLabel.linkActivated.disconnect()
        if not scan_clicked:
            self.main_window.deviceWindow.deviceLabel.linkActivated.connect(lambda _:
                                                                            self._device_scan_clicked(data[1], data[2]))

    def _device_scan_clicked(self, ip, mac):
        self.main_window.deviceWindow.deviceLabel.linkActivated.disconnect()
        self._update_device_window(self._dbagent.get_device_info(self.open_device_id), True)
        self.command_scanner(('scan_ports', (ip, mac)))

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
