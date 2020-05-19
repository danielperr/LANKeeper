# LANKeeper (https://github.com/danielperr/LANKeeper)
# Scanner

from scapy.all import *
from host import Host
from ports import COMMON_PORTS
from scanresult import ScanResult
from multiprocessing.pool import ThreadPool
import history as h
import IPy
import socket
import requests


NAME = 0b1
VENDOR = 0b10
PORTS = 0b100
OS = 0b1000

DEFAULT_ARP_TIMEOUT = 2  # sec
DEFAULT_PROG_INTERVAL = 10  # sec


class Scanner (object):

    options_flags = {
        NAME: 'name',
        VENDOR: 'vendor',
        PORTS: 'ports',
        OS: 'os'
    }

    def __init__(self, manager_conn, **kwargs):
        self._manager_conn = manager_conn
        self.scan_times = list()  # TODO Scanner scan times
        self.scapykwargs = kwargs

        while True:
            command = self._manager_conn.recv()
            if command:
                self._run_command(command)

    def _run_command(self, cmd):
        if isinstance(cmd, tuple):  # has args
            print('running command', cmd)
            eval('self.' + cmd[0])(*cmd[1])
        else:
            eval(cmd)()

    def scan(self, targets, options=0, **kwargs):
        ips = list()  # list of ip addresses we are going to scan
        for target in targets.split(','):
            try:
                ipy_target = IPy.IP(target.strip())
            except ValueError:
                raise ValueError('%s is not a valid ip address or network' % target)
            if len(ipy_target) > 1:  # Is a subnet
                ips += list(map(str, ipy_target))
            else:
                ips.append(str(ipy_target))
        timeout = DEFAULT_ARP_TIMEOUT
        if 'timeout' in kwargs.keys():
            timeout = kwargs['timeout']

        # Perform basic scans (ip <-> mac)
        # print('scanning')
        ipmac = dict()  # {ip: mac}

        def handle_is_at(p):
            ipmac[p.psrc] = p.hwsrc

        def threaded_sniff():
            sniff(filter='arp',
                  lfilter=lambda p: p.op == 2 and p.hwdst == conf.iface.mac,
                  prn=handle_is_at,
                  timeout=timeout)  # TODO - STOP SNIFF IF ALL TARGETS WERE DETECTED

        sniff_thread = threading.Thread(target=threaded_sniff, args=())
        sniff_thread.start()
        sendp([Ether(dst='ff:ff:ff:ff:ff:ff') / ARP(pdst=ip) for ip in ips],
              verbose=0, **self.scapykwargs)
        sniff_thread.join()

        hosts = sorted([Host(ip, mac) for ip, mac in ipmac.items()], key=lambda h: IPy.IP(h.ip))
        # print(list(map(str, hosts)))
        # print('%s hosts are up. Running scans...' % len(hosts))
        # print('\n'.join(map(str, hosts)))

        # Perform custom / optional scans
        def threaded_scan(h):
            try:
                self._scan(h, options)
            except ScanError:
                return

        threads = list()
        for host in hosts:
            thread = threading.Thread(target=threaded_scan, args=(host, ))
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()

        hosts = list(filter(lambda x: x.mac, hosts))
        # print('\n'.join(map(str, hosts)))
        # print('%s hosts up.' % len(hosts))
        print('sending scan results')
        scan_result = ScanResult(hosts, datetime.now(), bool(options == PORTS + OS))
        self._manager_conn.send(scan_result)
        return hosts

    def progressive_scan(self, targets, options=0, interval=DEFAULT_PROG_INTERVAL, **kwargs):
        """Repeatedly scans targets in timed intervals and writes changes to history
        :param history_obj: history object
        :param targets: targets to scans
        :param options: scan options
        :param interval: the time interval between scans in seconds
        :param kwargs: scapy kwargs"""
        while 1:
            if self._manager_conn.poll():
                self._run_command(self._manager_conn.recv())
            print('starting scan.')
            hosts = self.scan(targets, options, **kwargs)
            print('scan done.')
            time.sleep(interval)

    def scan_ports(self, ip, mac):
        """sends ScanResult object with ports"""
        host = Host(ip, mac)
        self._getports(host)
        self._manager_conn.send(ScanResult([host], datetime.now()))

    def _scan(self, host, options=0):
        """Given host must have IP and MAC addresses"""
        if not (host.ip and host.mac):
            raise ScanError('given host must have an ip')
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
        try:
            result = response.json()['result']
            host.vendor = '' if 'error' in result else result['company']
        except Exception:
            return

    def _getports(self, host):

        # def f(port):
        #     response = sr1(IP(dst=host.ip) / TCP(dport=port, flags='S'), timeout=0.3, verbose=0)
        #     if response:
        #         if response.haslayer(TCP) and response[TCP].flags == 'SA':
        #             print(port)
        #             host.ports.append(port)
        #             return port
        #     return 0

        # with ThreadPool(50) as pool:
        #     host.ports = list(filter(bool, pool.map(f, COMMON_PORTS)))

        # print('openports:', host.ports)

        # print(host.openports)

        # for port in COMMON_PORTS:
        #     response = sr1(IP(dst=host.ip) / TCP(dport=port, flags='S'), timeout=1, verbose=0)
        #     if response:
        #         if response.haslayer(TCP) and response[TCP].flags == 'SA':
        #             host.openports.append(port)
        # ans, unans = sr([IP(dst=host.ip) / TCP(dport=port, flags='S') for port in COMMON_PORTS],
        #                 verbose=0, multi=1, timeout=1)
        # for snt, recvd in ans:
        #     if recvd and recvd.haslayer(TCP) and recvd[TCP].flags == 0x12:  # SYN ACK = port open
        #         host.ports.append(recvd['TCP'].sport)
        ports = []

        def handle_response(p):
            ports.append(p.sport)

        def ports_threaded_sniff():
            sniff(filter='tcp',
                  lfilter=lambda p: p[TCP].flags == 0x12,
                  prn=handle_response,
                  timeout=5)  # TODO - STOP SNIFF IF ALL TARGETS WERE DETECTED

        sniff_thread = threading.Thread(target=ports_threaded_sniff, args=())
        sniff_thread.start()
        print('host ip:', host.ip)
        send([IP(dst=host.ip) / TCP(dport=port, flags='S') for port in COMMON_PORTS],
             verbose=1, **self.scapykwargs)
        sniff_thread.join()

        host.ports = list(set(ports))

        print('open ports:', host.ports)

    def _getos(self, host):
        host.os = 'Windows'


class ScanError (Exception):
    pass


if __name__ == '__main__':
    sc = Scanner()
    # sc.scan('10.100.102.0/24')
    # sc.scan('10.100.102.0/24', NAME + VENDOR)
    # sc.scan('10.100.102.22', PORTS)
    hs = h.History(new=1)
    # sc.progressive_scan(hs, '10.100.102.0/24', 0, 5)
    sc.progressive_scan(hs, ', '.join(['172.16.%s.0/24' % x for x in [0, 3, 10, 11, 12, 13]]), NAME + VENDOR, 1)
    # sc.progressive_scan(hs, '172.16.0.0/16', 0, 5)
