# LANKeeper (https://github.com/danielperr/LANKeeper)
# Struct for result of scanning

import datetime
import lankeeper.host


class ScanResult (object):

    def __init__(self,
                 hosts: list[lankeeper.host.Host],
                 starttime: datetime.datetime,
                 endtime: datetime.datetime):
        self.hosts = hosts
        self.starttime = starttime
        self.endtime = endtime
