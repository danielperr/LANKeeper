# LANKeeper (https://github.com/danielperr/LANKeeper)
# Looks for duplicate MAC addresses and flags them

from detectors.base_detector import BaseDetector


class ARPSpoofDetector (BaseDetector):

    name = 'ARP spoofing'

    def __init__(self, forbidden_domains: [str]):
        pass

    def handle_packet(self, p):
        pass

    def detect(self):
        return []


if __name__ == '__main__':
    pass
