# LANKeeper (https://github.com/danielperr/LANKeeper)
# TCP SYN flood detector
from detectors.basedetector import BaseDetector
from scapy.all import *
import datetime
import time


class Host (object):

    sample_size = 10  # look at the last x packets

    def __init__(self, ip):

        self.ip = ip  # machine ip
        self.rate = 0.0  # packets recieved from it per second
        self.time_points = list()  # time points when the packets from this host are recieved

    def append_time_point(self):

        if len(self.time_points) >= self.sample_size:
            del self.time_points[0]
        ticks = (datetime.datetime.now() - datetime.datetime(1, 1, 1)).total_seconds()
        self.time_points.append(ticks)
        self._calculate_rate()

    def _calculate_rate(self):
        # print(self.time_points)
        time_deltas = [self.time_points[i+1] - self.time_points[i] for i in range(len(self.time_points) - 1)]
        if not time_deltas:
            return
        try:
            self.rate = len(time_deltas) / sum(time_deltas)
        except ZeroDivisionError:
            return
        # print('%s at %s pkts/sec' % (self.ip, self.rate))


class TcpSynFloodDetector (BaseDetector):

    name = 'TCP flood attack'
    detect_rate = 10  # pkts/sec

    def __init__(self):
        self.hosts = list()

    def handle_packet(self, p):
        if p.haslayer(TCP) and p[TCP].flags & 0x02:  # SYN
            ip = p[IP].src
            host = self._get_host(ip)
            if not host:
                host = Host(ip)
                self.hosts.append(host)
            host.append_time_point()

    def detect(self):
        return list(map(lambda x: x.ip, filter(lambda x: x.rate > self.detect_rate, self.hosts)))

    def _get_host(self, ip: str):
        for host in self.hosts:
            if host.ip == ip:
                return host
        return None


if __name__ == '__main__':
    print('Starting')
    detector = TcpSynFloodDetector()
    sniff(filter='ip', prn=detector.handle_packet, stop_filter=lambda _: bool(detector.detect()))
    print(detector.detect())
    # print('\n')
    print('\n'.join(map(lambda x: '%s = %s pkts/sec' % (x.ip, x.rate), sorted(detector.hosts, key=lambda x: x.rate))))
