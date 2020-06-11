# LANKeeper (https://github.com/danielperr/LANKeeper)
# Looks for duplicate IP addresses and flags them

from scapy.all import *

from detectors.base_detector import BaseDetector


class IPDuplicationDetector (BaseDetector):

    name = 'IP duplication'

    def __init__(self, report):
        self.report = report
        self.susp = []
        self._ip_mac = {}  # {ip: mac}

    def handle_packet(self, p):
        if p.haslayer(IP) and p.haslayer(Ether):
            psrc = p[IP].src
            hwsrc = p[Ether].src
            if psrc in self._ip_mac.keys():
                if hwsrc != self._ip_mac[psrc]:
                    print(f'{psrc} : {hwsrc}')
                    self.report(psrc)
            else:
                self._ip_mac[psrc] = hwsrc

    def detect(self):
        return self.susp


if __name__ == '__main__':
    pass
