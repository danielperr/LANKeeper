# LANKeeper (https://github.com/danielperr/LANKeeper)
from abc import ABC, abstractmethod
from scapy.all import packet as scapypacket


class BaseDetector (ABC):
    """Detector abstract base class"""

    def name(self):
        """Name of the detector to appear on lists and menus"""
        raise NotImplementedError

    def report(self):
        """Callback function to report.
        Accepts IP address (str)"""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def handle_packet(cls, packet: scapypacket):
        """Recieve a packet from sniff"""
        pass
