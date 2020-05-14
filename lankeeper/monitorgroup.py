# LANKeeper (https://github.com/danielperr/LANKeeper)
# Monitoring Group


class MonitorGroup:

    def __init__(self, name, ips=[], detectors=[]):
        self.name = name
        self.detectors = detectors
        self.ips = ips

    def __str__(self):
        return f'Monitor group {self.name} consists of {len(self.ips)}' + \
               f' hosts and applies {len(self.detectors)} detectors'
