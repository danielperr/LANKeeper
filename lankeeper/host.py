# LANKeeper (https://github.com/danielperr/LANKeeper)
# Remote host machine struct


class Host (object):

    def __init__(self,
                 ip: str,
                 mac: str = '',
                 name: str = '',
                 vendor: str = '',
                 ports: list = [],
                 os: str = ''):
        self.ip = ip
        self.mac = mac
        self.name = name
        self.vendor = vendor
        self.ports = ports
        self.os = os
        # other attributes
        self.ttl = 0  # 0=unknown

    def __str__(self):
        return '%s%s - %s%s%s%s' % (
            self.ip,
            ' (%s)' % self.name if self.name else '',
            self.mac,
            ' (%s)' % self.vendor if self.vendor else '',
            ' running %s' % self.os if self.os else '',
            '\nPorts: [%s]' % ', '.join(map(str, self.ports)) if self.ports else ''
        )
