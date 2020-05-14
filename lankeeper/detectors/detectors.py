# LANKeeper (https://github.com/danielperr/LANKeeper)
# Import all detectors and pack them in a list

from detectors.tcpsynflooddetector import TcpSynFloodDetector

# NOTE do not change order, only append at the end
detectors = [
    TcpSynFloodDetector  # 0
]
detectors_sorted = sorted(detectors, key=lambda x: x.name)

default_detectors = [0]  # IDs of detectors in the default monitoring group
