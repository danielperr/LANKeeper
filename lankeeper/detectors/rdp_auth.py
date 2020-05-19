# LANKeeper (https://github.com/danielperr/LANKeeper)
# Looks for multiple trials of authenticating via RDP

from detectors.base_detector import BaseDetector


class RDPAuthDetector (BaseDetector):

    name = 'RDP authentication attempt'

    def __init__(self, forbidden_domains: [str]):
        pass

    def handle_packet(self, p):
        pass

    def detect(self):
        return []


if __name__ == '__main__':
    pass
