# LANKeeper (https://github.com/danielperr/LANKeeper)

import os


class Firewall (object):

    def __init__(self):
        self.blocked_ips = list()

    def fetch_rules(self):
        """Fetch advfirewall rules and update the list"""
        # output = os.system('netsh advfirewall firewall show rule name=all | find "Rule Name:" | find "Virtual"')
        # rules = output.split('\n').strip('Rule Name:').strip()
        # print(rules)
        pass

    def block_ip(self, ip):
        # os.system('netsh advfirewall firewall add rule name="Block %s" dir=in action=block remoteip=%s' % (ip, ip))
        pass