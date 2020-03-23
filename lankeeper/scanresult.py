# LANKeeper (https://github.com/danielperr/LANKeeper)
# Struct for scan result

from host import Host
import datetime


class ScanResult (object):

    def __init__(self,
                 hosts: list,
                 time: datetime.datetime):
        self.hosts = hosts
        self.time = time

    def __str__(self):
        return '%s scan result: (%s hosts up)\n:%s' % (self.time.strftime(r'%m/%d/%Y@%H:%M:%S'),
                                                       len(self.hosts),
                                                       '\n'.join(map(str, self.hosts)))
