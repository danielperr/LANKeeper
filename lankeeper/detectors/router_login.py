# LANKeeper (https://github.com/danielperr/LANKeeper)
# Monitors HTTP login attempts to the router and notifies about multiple trials

from detectors.base_detector import BaseDetector


class RouterLoginDetector (BaseDetector):

    name = 'Router login attempt'

    def __init__(self):
        pass

    def handle_packet(self, p):
        pass

    def detect(self):
        return []


if __name__ == '__main__':
    pass
