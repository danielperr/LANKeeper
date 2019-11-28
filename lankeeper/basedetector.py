# LANKeeper (https://github.com/danielperr/LANKeeper)
from abc import ABC, abstractmethod
from scapy.all import packet as scapypacket


class BaseDetector (ABC):

    @classmethod
    @abstractmethod
    def handle_packet(cls, packet: scapypacket):
        """Recieve a packet from sniff"""
        pass

    @classmethod
    @abstractmethod
    def detect(cls) -> list:
        """:returns str list of suspicious ips"""
        pass
