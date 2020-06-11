# LANKeeper (https://github.com/danielperr/LANKeeper)
from scapy.all import sniff
from accepts import accepts
import os
import re


class FirewallError (Exception):
    pass


class Firewall (object):

    rule_prefix = 'LANKeeper - '

    def __init__(self):
        self.blocked_ips = list()
        self.fetch_rules()

    def fetch_rules(self):
        """Fetch advfirewall rules and update the list"""
        output = os.popen('netsh advfirewall firewall show rule name=all | find "Rule Name:" | find "%s"'
                          % self.rule_prefix).read()
        rule_names = list(map(lambda x: re.sub(r'^Rule Name:\s*', '', x), output.split('\n')[:-1]))
        self.blocked_ips = list(map(lambda x: x.lstrip(self.rule_prefix), rule_names))

    def block_ip(self, ip: str):
        if ip in self.blocked_ips:
            return
        response = os.popen('netsh advfirewall firewall add rule name="%s%s" dir=in action=block remoteip=%s'
                            % (self.rule_prefix, ip, ip)).read()
        if 'Ok.' not in response:
            raise FirewallError(response)
        self.blocked_ips.append(ip)

    def unblock_ip(self, ip: str):
        if ip not in self.blocked_ips:
            return
        response = os.popen('netsh advfirewall firewall delete rule name="%s%s"' % (self.rule_prefix, ip)).read()
        if 'Ok.' not in response:
            raise FirewallError(response)
        try:
            self.blocked_ips.remove(ip)
        except ValueError:
            self.fetch_rules()


if __name__ == '__main__':
    fw = Firewall()
    # unblock ips from previous tests
    fw.fetch_rules()
    for blocked_ip in fw.blocked_ips:
        fw.unblock_ip(blocked_ip)
    fw.fetch_rules()
    print(fw.blocked_ips)
    # sniff and forward packets to the fw
    sniff(filter='tcp', prn=fw.handle_packet)
