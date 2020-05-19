# LANKeeper (https://github.com/danielperr/LANKeeper)

from datetime import datetime


class MonitorEvent:

    TRAFFIC = 0
    PROCESS = 1
    DRIVE = 2

    def __init__(self,
                 id_: int,
                 ip: str,
                 time: datetime,
                 type: int,
                 ignore: bool,
                 *_,
                 action: str = '',
                 process: str = '',
                 drive: str = ''):
        self.id = id_
        self.ip = ip
        self.type = type
        self.ignore = ignore
        self.action = action
        self.process = process
        self.drive = drive
