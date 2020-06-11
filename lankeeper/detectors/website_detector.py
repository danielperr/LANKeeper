# LANKeeper (https://github.com/danielperr/LANKeeper)
# This detector is used for forbidden websites and will not be included in the configuration lists

from socket import getaddrinfo
from detectors.base_detector import BaseDetector
from scapy.all import *


class WebsiteDetector (BaseDetector):

    def __init__(self, addrs: list, report):
        """
        :param addrs: list of forbidden addresses in str (domain or IPv4)
        :param report: callback function to report activity; accepts (ip_address: str, website_accessed: str)
        """
        self.report = report
        # split to forbidden domains and ips
        addrs = filter(lambda addr: ':' not in addr, addrs)  # filter out IPv6
        self.frb_domains = [addr for addr in addrs if any([c.isalpha() for c in addr])]
        self.frb_ips = [addr for addr in addrs if addr not in self.frb_domains]
        self.domain_ips = {  # {domain_name: [ip, ip, ...]}
            domain: list(set([x[4][0] for x in getaddrinfo(domain, 80) + getaddrinfo(domain, 443)]))
            for domain in self.frb_domains
        }
        print(self.domain_ips)

    def handle_packet(self, p):
        psrc, pdst = p[IP].src, p[IP].dst
        if pdst in self.frb_ips:  # client to server
            self.report(psrc, pdst)
        elif psrc in self.frb_ips:  # server to client
            self.report(pdst, psrc)
        else:
            for domain, ips in self.domain_ips.items():
                if pdst in ips:  # client to server
                    self.report(psrc, domain)
                elif psrc in ips:  # server to client
                    self.report(pdst, domain)


def report(ip, website):
    print(f'{ip=} {website=}')


if __name__ == '__main__':
    print('starting')
    d = WebsiteDetector(['ksp.co.il', 'fxp.co.il', 'weizmann.ac.il', 'net-games.co.il'], report)
    sniff(filter='ip', prn=d.handle_packet)
