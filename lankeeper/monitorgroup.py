# LANKeeper (https://github.com/danielperr/LANKeeper)
# Monitoring Group


class MonitorGroup:

    WMI_PROC = 1
    WMI_DRIV = 2

    def __init__(self, name, ips=[], detectors=[], wmi=3, websites=[]):
        """
        websites (list): Forbidden websites (can be domain name or IP address)
        """
        self.name = name
        self.ips = ips
        self.detectors = detectors
        self.wmi = wmi
        self.websites = websites

    def __str__(self):
        return f'Monitor group {self.name} ; Hosts: {len(self.ips)} ; Detectors: {len(self.detectors)} ; ' \
               f'WMI mode: {self.wmi} ; Forbidden websites: {len(self.websites)}'
