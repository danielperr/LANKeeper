# LANKeeper (https://github.com/danielperr/LANKeeper)
# Detects smurf attack

from detectors.base_detector import BaseDetector


class SmurfAttackDetector (BaseDetector):

    name = 'Smurf attack'

    def __init__(self, forbidden_domains: [str]):
        pass

    def handle_packet(self, p):
        pass

    def detect(self):
        return []


if __name__ == '__main__':
    pass
