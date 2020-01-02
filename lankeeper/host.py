# LANKeeper (https://github.com/danielperr/LANKeeper)
# Remote host machine struct

import IPy


class Host (object):
    
    def __init__(self,
                 ip: IPy.IP,
                 mac: str = '',
                 name: str = '',
                 vendor: str = '',
                 openports: list = []):
        self.ip = ip
        self.mac = mac
        self.name = name
        self.vendor = vendor
        self.openports = openports
