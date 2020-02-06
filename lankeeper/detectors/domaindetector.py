# LANKeeper (https://github.com/danielperr/LANKeeper)
# TCP SYN flood detector
from detectors.basedetector import BaseDetector
from scapy.all import *


class DomainDetector (BaseDetector):

    detect_rate = 10  # pkts/sec

    def __init__(self, forbidden_domains: [str]):
        self.ips = dict()
        self.forbidden = forbidden_domains

    def handle_packet(self, p):
        if p.haslayer('DNS'):
            for domain in self.forbidden:
                if domain in p['DNS'].qd[0].qname.decode('ASCII'):
                    self.ips[(p['IP'].src)] = domain

    def detect(self):
        return self.ips


if __name__ == '__main__':
    print('Starting')
    detector = DomainDetector('coolmathgames.com')
    sniff(filter='ip', prn=detector.handle_packet, stop_filter=lambda _: bool(detector.detect()))
    print(detector.detect())
