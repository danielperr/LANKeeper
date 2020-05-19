# LANKeeper (https://github.com/danielperr/LANKeeper)
# The Device class extends Host (which is an entity in a network) and adds GUI relevant attributes

from datetime import datetime
from host import Host


class Device (Host):

    DATETIME_FORMAT = r'%m/%d/%Y at %H:%M:%S'

    def __init__(self,
                 id_: int,
                 ip: str,
                 mac: str = '',
                 name: str = '',
                 vendor: str = '',
                 ports: list = [],
                 os: str = '',
                 first_joined: datetime = datetime.now(),
                 last_seen: datetime = datetime.now(),
                 mg_id: int = 1,
                 new_device: bool = False):
        super().__init__(ip=ip,
                         mac=mac,
                         name=name,
                         vendor=vendor,
                         ports=ports,
                         os=os)
        self.id = id_
        self.first_joined = first_joined
        self.last_seen = last_seen
        self.mg_id = mg_id
        self.new_device = new_device
        self.monitor_events = []

    def __str__(self):
        return '%s\nFirst joined: %s\nLast seen: %s\nBelongs to monitor group ID %s\nMonitor events: %s' % (
            super().__str__(),
            self.first_joined.strftime(self.DATETIME_FORMAT),
            self.last_seen.strftime(self.DATETIME_FORMAT),
            self.mg_id,
            len(self.monitor_events)
        )
