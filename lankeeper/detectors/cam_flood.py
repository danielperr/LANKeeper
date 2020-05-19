# LANKeeper (https://github.com/danielperr/LANKeeper)
# Flags devices that send fake ARP info at high speeds

from detectors.base_detector import BaseDetector


class CAMFloodDetector (BaseDetector):

    name = 'CAM flood attack'

    def __init__(self, forbidden_domains: [str]):
        pass

    def handle_packet(self, p):
        pass

    def detect(self):
        return []


if __name__ == '__main__':
    pass
