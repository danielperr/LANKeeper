# LANKeeper (https://github.com/danielperr/LANKeeper)
# Looks for duplicate IP addresses and flags them

from detectors.base_detector import BaseDetector


class IPDuplicationDetector (BaseDetector):

    name = 'IP duplication'

    def __init__(self, forbidden_domains: [str]):
        pass

    def handle_packet(self, p):
        pass

    def detect(self):
        return []


if __name__ == '__main__':
    pass
