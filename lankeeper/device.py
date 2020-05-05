from host import Host

from datetime import datetime


class Device (Host):

    DATETIME_FORMAT = r'%m/%d/%Y at %H:%M:%S'

    def __init__(self, ip: str, *,
                 mac: str = '',
                 name: str = '',
                 vendor: str = '',
                 ports: list = [],
                 first_joined: datetime,
                 last_seen: datetime):
        super().__init__(ip=ip,
                         mac=mac,
                         name=name,
                         vendor=vendor,
                         ports=ports)
        self.first_joined = first_joined
        self.last_seen = last_seen

    def __str__(self):
        return '%s\nFirst joined: %s\nLast seen: %s' % (
            super().__str__(),
            self.first_joined.strftime(self.DATETIME_FORMAT),
            self.last_seen.strftime(self.DATETIME_FORMAT)
        )
