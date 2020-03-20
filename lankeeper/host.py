# LANKeeper (https://github.com/danielperr/LANKeeper)
# Remote host machine struct

TEXT_NORMAL = '\033[0m'
TEXT_BOLD = '\033[1m'


class Host (object):

    def __init__(self,
                 ip: str,
                 mac: str = '',
                 name: str = '',
                 vendor: str = '',
                 ports: list = []):
        self.ip = ip
        self.mac = mac
        self.name = name
        self.vendor = vendor
        self.ports = ports

    def __str__(self):
        return '\033[4m%s\033[0m%s - \033[4m%s\033[0m%s%s' % (
            self.ip,
            ' (%s)' % self.name if self.name else '',
            self.mac,
            ' (%s)' % self.vendor if self.vendor else '',
            '\nPorts: [%s]' % ', '.join(map(str, self.ports)) if self.ports else ''
        )
