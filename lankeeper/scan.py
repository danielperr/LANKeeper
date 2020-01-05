# LANKeeper (https://github.com/danielperr/LANKeeper)
# Scanner

from scapy.all import *
from host import Host
import IPy
import socket
import requests


class Scanner (object):

    options_flags = {
        0x1: 'name',
        0x2: 'vendor',
        0x4: 'ports'
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

        hosts = [Host(ip) for ip in ips]
        for host in hosts:
            self._scan(host, options)
        print('\n'.join(map(str, hosts)))

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
        pass


class ScanError (Exception):
    pass


if __name__ == '__main__':
    sc = Scanner()
    # sc.scan('10.100.102.0/24')
    sc.scan('10.100.102.1', 7)
