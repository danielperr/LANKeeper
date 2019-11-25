# LANKeeper (https://github.com/danielperr/LANKeeper)

from scapy.all import *

import IPy
import socket
import requests


class Scanner (object):
    """Early version subnet scanner"""

    def __init__(self, targets, **kwargs):
        """
        :param targets: Network target/s to scan e.g. "10.10.10.1, 10.10.10.3, 10.10.14.0/24"
        :param kwargs: Scapy kwargs
        """
        self.scapykwargs = kwargs
        self.targets = list()
        for target in map(lambda x: x.strip(), targets.split(',')):
            try:
                self.targets += list(map(str, IPy.IP(target)))
            except ValueError:
                raise ValueError('invalid target %s' % target)
        self.hosts = list()  # [{'ip': ..., 'mac': ..., 'name': ...}, ]

    def pingscan(self, **kwargs):
        """Performs a ping (arp) scan on the subnet hosts"""
        verbose = 'verbose' in kwargs.keys() and kwargs['verbose']
        if verbose:
            print('Starting scan')

        ans, unans = srp([Ether(dst='ff:ff:ff:ff:ff:ff') / ARP(pdst=target) for target in self.targets]
                         , multi=1, verbose=0, timeout=1, **self.scapykwargs)

        count = 0
        for snt, recvd in ans:
            if recvd:
                hostip = recvd[ARP].psrc
                hostmac = recvd[ARP].hwsrc
                self.hosts.append({'ip': hostip, 'mac': hostmac})
                count += 1
                if verbose:
                    print('Scan report for %s\nHost is up (%.2fs latency)\nMAC Address: %s\n'
                      % (hostip, recvd.time-snt.time, hostmac))

        if verbose:
            print('Scan report for %s:\nHost is up.\nMAC Address: %s\n'
                  % (conf.iface.ip, conf.iface.mac))  # This machine
            if not count:
                print('Done: %s IP addresses (1 host up) scanned' % len(self.targets))
            else:
                print('Done: %s IP addresses (%s hosts up) scanned in %.2f seconds'
                      % (len(self.targets), count+1, ans[1][-1].time - ans[0][0].time))

    # def portscan(self, hosts=None, **kwargs):
    #     """Performs port scans on already discovered ips"""
    #     if not hosts:
    #         hosts = self.hosts
    #     if not hosts:
    #         raise IndexError('no hosts are given / previously discovered / up')
    #
    #     verbose = 'verbose' in kwargs.keys() and kwargs['verbose']
    #     if verbose:
    #         print 'Starting port scan'
    #
    #     for host in hosts:
    #         host['ports'] = list()
    #         # for port in range(65535):
    #         #     response = sr1(IP(dst=host['ip']) / TCP(dport=port, flags='S'), timeout=1)
    #         #     if response:
    #         #         if response.haslayer(TCP) and response[TCP].flags == 'SA':
    #         #             host['ports'].append(port)
    #         ans, unans = sr([IP(dst=host['ip']) / TCP(dport=port, flags='S') for port in range(9999)]
    #                         , multi=1, verbose=0, timeout=0.1, **self.scapykwargs)
    #         for snt, recvd in ans:
    #             if recvd and recvd.haslayer(TCP) and recvd[TCP].flags == 0x12:  # SYN ACK = port open
    #                 host['ports'].append(recvd['TCP'].sport)
    #         if verbose:
    #             print 'Open ports for %s:\n - %s' % (host['ip'], '\n - '.join(host['ports']))

    def resolve_names(self, **kwargs):
        """Performs host name scans on already discovered ips"""
        if not self.hosts:
            raise IndexError('no hosts are given / previously discovered / up')

        verbose = 'verbose' in kwargs.keys() and kwargs['verbose']
        if verbose:
            print('Starting name resolution')

        count = 0
        for host in self.hosts:
            try:
                name = socket.gethostbyaddr(host['ip'])[0]
                if not name:
                    continue
                host['name'] = name
                count += 1
                if verbose:
                    print("%s (%s)" % (name, host['ip']))
            except socket.herror:
                continue

        if verbose:
            print('Done: %s hosts scanned, %s identified' % (len(self.hosts), count))

    def resolve_vendors(self, **kwargs):
        """Resolves vendor on already discovered mac addresses"""
        if not self.hosts:
            raise IndexError('no hosts are given / previously discovered / up')

        verbose = 'verbose' in kwargs.keys() and kwargs['verbose']
        if verbose:
            print('Starting vendor lookup')

        count = 0
        for host in self.hosts:
            response = requests.get('http://macvendors.co/api/' + host['mac'])
            result = response.json()['result']
            host['vendor'] = 'unknown' if 'error' in result else result['company']
            if host['vendor'] != 'unknown':
                count += 1
            if verbose:
                print('%s (%s)' % (host['mac'].upper(), host['vendor']))

        if verbose:
            print('Done: %s hosts scanned, %s identified' % (len(self.hosts), count))


if __name__ == '__main__':
    scanner = Scanner('10.100.102.0/24')
    scanner.pingscan(verbose=1); print('\n\n')
    # # scanner.portscan(verbose=1);
    scanner.resolve_names(verbose=1); print('\n\n')
    scanner.resolve_vendors(verbose=1)
    # scanner.portscan([{'ip': '10.100.102.15'}], verbose=1)
