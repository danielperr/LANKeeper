# LANKeeper (https://github.com/danielperr/LANKeeper)
# Import all detectors and pack them in a list

from detectors.tcp_flood import TcpFloodDetector
from detectors.ip_duplication import IPDuplicationDetector
from detectors.rdp_auth import RDPAuthDetector
from detectors.router_login import RouterLoginDetector
from detectors.smurf_attack import SmurfAttackDetector

# NOTE do not change order, only append to the end
detectors = [
    TcpFloodDetector,  # this one's ID is 0 and so on
    IPDuplicationDetector,
    RouterLoginDetector
]

detectors_sorted = sorted(detectors, key=lambda x: x.name)

default_detectors = [0]  # IDs of detectors in the default monitoring group
