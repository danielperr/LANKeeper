# LANKeeper (https://github.com/danielperr/LANKeeper)
# Remote host machine struct


class Host (object):
    
    def __init__(self,
                 ip: str,
                 mac: str = '',
                 name: str = '',
                 vendor: str = '',
                 openports: list = []):
        self.ip = ip
        self.mac = mac
        self.name = name
        self.vendor = vendor
        self.openports = openports

    def __str__(self):
        return '%s (%s)\n%s (%s)\nports: %s'\
               % (self.ip, self.name, self.mac, self.vendor, self.openports)
