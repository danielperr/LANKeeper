# LANKeeper (https://github.com/danielperr/LANKeeper)
# Scanner

from scapy.all import *
from host import Host
import IPy
import socket
import requests


NAME = 0b1
VENDOR = 0b10
PORTS = 0b100


class Scanner (object):

    options_flags = {
        NAME: 'name',
        VENDOR: 'vendor',
        PORTS: 'ports'
    }

    def __init__(self):
        self.scan_times = list()  # TODO Scanner scan times

    def scan(self, targets, options=0):

        ips = list()
        for target in targets.split(','):
            try:
                ipy_target = IPy.IP(target.strip())
            except ValueError:
                raise ValueError('%s is not a valid ip address or network' % target)
            if len(ipy_target) > 1:  # Is a subnet
                ips += list(map(str, ipy_target))
            else:
                ips.append(str(ipy_target))

        def threaded_scan(h):
            try:
                self._scan(h, options)
            except ScanError:
                return

        hosts = [Host(ip) for ip in ips]
        threads = list()
        for host in hosts:
            thread = threading.Thread(target=threaded_scan, args=(host, ))
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()

        hosts = list(filter(lambda x: x.mac, hosts))
        print('\n'.join(map(str, hosts)))
        print('%s Hosts up + 1 (me)' % len(hosts))

    def _scan(self, host, options=0):
        if not host.ip:
            raise ScanError('given host must have an ip')
        if not host.mac:
            ans = srp1(Ether(dst=ETHER_BROADCAST) / ARP(pdst=host.ip), verbose=0, timeout=5)
            if ans:
                host.mac = ans.hwsrc
            else:
                raise ScanError('given host does not seem up')
        for flagnum, flagname in self.options_flags.items():
            if flagnum & options:
                exec('self._get%s(host)' % flagname)

    def _getname(self, host):
        try:
            host.name = socket.gethostbyaddr(host.ip)[0]
        except socket.herror:
            return

    def _getvendor(self, host):
        response = requests.get('http://macvendors.co/api/' + host.mac)
        result = response.json()['result']
        host.vendor = '' if 'error' in result else result['company']

    def _getports(self, host):
        host.openports = list()
        # for port in range(65535):
        #     response = sr1(IP(dst=host['ip']) / TCP(dport=port, flags='S'), timeout=1)
        #     if response:
        #         if response.haslayer(TCP) and response[TCP].flags == 'SA':
        #             host['ports'].append(port)
        ans, unans = sr([IP(dst=host.ip) / TCP(dport=port, flags='S') for port in range(9999)]
                        , verbose=0, multi=1, timeout=1)
        for snt, recvd in ans:
            if recvd and recvd.haslayer(TCP) and recvd[TCP].flags == 0x12:  # SYN ACK = port open
                host.openports.append(recvd['TCP'].sport)


class ScanError (Exception):
    pass


if __name__ == '__main__':
    sc = Scanner()
    # sc.scan('10.100.102.0/24')
    sc.scan('10.100.102.0/24', NAME + VENDOR)
