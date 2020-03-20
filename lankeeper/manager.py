from multiprocessing import Process, Pipe
from queue import Queue
import ctypes

import sys

import scan as s
import history as h


class Manager:

    def __init__():

        self.scanner_queue = Queue()

        self.scanner_conn, scanner_side = Pipe()

        scanner_object = s.Scanner
        self.scanner_process = Process(
            target=scanner_object,
            args=(scanner_side, ))
        self.scanner_process.daemon = True

        print('starting scanner process')
        self.scanner_process.start()

        conn_list = [scanner_conn]

        while True:
            readables = list(filter(lambda c: c.poll(), conn_list))

            for readable in readables:
                print(str(readable.recv()))

            if not self.scanner_queue.empty():
                self.scanner_conn.send(scanner_queue.get())

        self.scanner_process.join()

    def command_scanner(command):
        self.scanner_queue.put(command)


def main():
    if is_admin():
        try:
            m = Manager()
            m.command_scanner(('progressive_scan', ('10.100.102.0/24', s.NAME + s.VENDOR)))
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
