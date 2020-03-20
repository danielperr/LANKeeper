from multiprocessing import Process, Pipe
from queue import Queue
import ctypes

import sys

import scan as s
import history as h
from dbagent import DBAgent
from scanresult import ScanResult


class Manager:

    def __init__(self):

        self._dbagent = DBAgent(new=1)

        self.scanner_queue = Queue()
        self.scanner_conn, scanner_side = Pipe()
        self.scanner_process = Process(
            target=s.Scanner,
            args=(scanner_side, ))
        self.scanner_process.daemon = True

    def start(self):

        self.scanner_process.start()

        while True:
            readables = list(filter(lambda c: c.poll(), [self.scanner_conn]))
            for readable in readables:
                data = readable.recv()
                if isinstance(data, ScanResult):
                    self._dbagent.add_scan_result(data)
            if not self.scanner_queue.empty():
                self.scanner_conn.send(self.scanner_queue.get())

        self.scanner_process.join()

    def command_scanner(self, command):
        self.scanner_queue.put(command)


def main():
    if is_admin():
        try:
            m = Manager()
            m.command_scanner(('progressive_scan', ('10.100.102.0/24', s.NAME + s.VENDOR)))
            m.start()
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
