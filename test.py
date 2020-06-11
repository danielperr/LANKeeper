from scapy.all import *
from socket import getaddrinfo


SNIFF_IP = '10.100.102.34'
FORBIDDEN = ['fxp.co.il', 'ksp.co.il', 'net-games.co.il', 'weizmann.ac.il']

forbidden_ips = []


def handle_packet(p):
    psrc, pdst = p[IP].src, p[IP].dst
    if pdst in forbidden_ips or psrc in forbidden_ips:
        # print(f'{psrc} > {pdst}')
        print('oh no')


def main():
    global forbidden_ips
    # resolve forbidden domains
    for domain in FORBIDDEN:
        forbidden_ips += list(set([x[4][0] for x in getaddrinfo(domain, 80) + getaddrinfo(domain, 443)]))
    print(forbidden_ips)
    sniff(lfilter=lambda p: p.haslayer(IP) and (p[IP].src == SNIFF_IP or p[IP].dst == SNIFF_IP),
          prn=handle_packet)


if __name__ == "__main__":
    main()
