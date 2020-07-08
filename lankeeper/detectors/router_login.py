# LANKeeper (https://github.com/danielperr/LANKeeper)
# Monitors HTTP login attempts to the router and notifies about multiple trials

try:
    from detectors.base_detector import BaseDetector
except ModuleNotFoundError:  # local testing
    from base_detector import BaseDetector
from scapy.all import *


class RouterLoginDetector (BaseDetector):

    name = 'Router login attempt'

    def __init__(self, report):
        self.report = report
        self.router_ip = [x[2] for x in conf.route.routes if x[2] != '0.0.0.0'][0]

    def handle_packet(self, p):
        if p[IP].dst == self.router_ip and p.haslayer(TCP) and p[TCP].dport == 80 and 'POST' in str(p):
            self.report(p[IP].src)


def report(ip):
    print(f'{ip} has tried to login to the router')
    exit()


if __name__ == '__main__':
    print('starting')
    d = RouterLoginDetector(report)
    sniff(filter='ip', prn=d.handle_packet)
