# LANKeeper (https://github.com/danielperr/LANKeeper)
# Monitoring Group


class MonitorGroup:

    def __init__(self, name, ips=[], detectors=[], websites=[]):
        """
        websites (list): Forbidden websites (can be domain name or IP address)
        """
        self.name = name
        self.ips = ips
        self.detectors = detectors
        self.websites = websites

    def __str__(self):
        return f'Monitor group {self.name} consists of {len(self.ips)}' + \
               f' hosts, applies {len(self.detectors)} detectors and ' + \
               (f'forbids these websites: {", ".join(self.websites)}'
                if self.websites else 'does not forbid access to websites.')
