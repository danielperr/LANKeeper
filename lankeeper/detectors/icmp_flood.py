# LANKeeper (https://github.com/danielperr/LANKeeper)
# TCP SYN flood detector
from detectors.base_detector import BaseDetector
from scapy.all import *
import datetime
import time


class Host (object):

    sample_size = 10  # look at the last x packets

    def __init__(self, ip):

        self.ip = ip  # machine ip
        self.rate = 0.0  # packets recieved from it per second
        self.time_points = list()  # time points when the packets from this host are recieved
        self.reported = False

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


class IcmpFloodDetector (BaseDetector):

    name = 'ICMP Denial of Service'
    detect_rate = 1000  # pkts/sec

    def __init__(self, report):
        self.report = report
        self.hosts = list()

    def handle_packet(self, p):
        if p.haslayer(ICMP) and p[ICMP].code == 0:
            ip = p[IP].src
            print(p.summary())
            host = self._get_host(ip)
            if not host:
                host = Host(ip)
                self.hosts.append(host)
            host.append_time_point()
            for host in self.hosts:
                if host.rate > self.detect_rate and not host.reported:
                    host.reported = True
                    self.report(host.ip)
                elif host.reported and host.rate < self.detect_rate:
                    host.reported = False

    def _get_host(self, ip: str):
        for host in self.hosts:
            if host.ip == ip:
                return host
        return None


if __name__ == '__main__':
    pass
