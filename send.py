import socket
import sys
import time

from scapy.all import *
from scapy.packet import Packet
from scapy.fields import ByteField, ShortField, IntField, IPField, StrFixedLenField, ShortEnumField, XShortField

def get_if():
    ifs = get_if_list()
    iface = None
    for i in get_if_list():
        if "eth0" in i:
            iface = i
            break
    if not iface:
        print("Cannot find eth0 interface")
        exit(1)
    return iface


def create_ipv4_packet(dst_addr):
    pkt = Ether(src=get_if_hwaddr(get_if()), dst='ff:ff:ff:ff:ff:ff')
    pkt = pkt / IP(dst=dst_addr)
    return pkt


def create_udp_packet(dst_addr, dst_port):
    pkt = Ether(src=get_if_hwaddr(get_if()), dst='ff:ff:ff:ff:ff:ff')
    pkt = pkt / IP(dst=dst_addr) / UDP(sport=12345, dport=dst_port)
    return pkt


def create_dhcp_block_packet(dst_addr):
    pkt = Ether(src=get_if_hwaddr(get_if()), dst='ff:ff:ff:ff:ff:ff')
    pkt = pkt / IP(src='10.0.0.10', dst=dst_addr, proto=17) / UDP(sport=67, dport=68) / BOOTP(ciaddr='10.0.0.10')
    return pkt

def create_dhcp_regular_packet(dst_addr):
    pkt = Ether(src=get_if_hwaddr(get_if()), dst='ff:ff:ff:ff:ff:ff')
    pkt = pkt / IP(src='10.0.0.10', dst=dst_addr, proto=17) / UDP(sport=67, dport=68) / BOOTP(ciaddr='10.0.0.10')
    return pkt


def main():

    if len(sys.argv) < 2:
        print('pass 2 arguments: <destination> "<message>"')
        exit(1)

    addr = socket.gethostbyname(sys.argv[1])
    iface = get_if()

    print("sending on interface %s to %s" % (iface, str(addr)))

    # pkt = create_ipv4_packet(addr)
    # pkt = create_udp_packet(addr, 80)
    pkt = create_dhcp_packet(addr)

    # Send packets at 10Mbps for 30 seconds
    start_time = time.time()
    end_time = start_time + 25
    pkt_size = len(pkt) * 8
    interval = pkt_size / (10 * 1024 * 1024)

    packets_sent = 0

    while time.time() < end_time:
        sendp(pkt, iface=iface, verbose=False)
        packets_sent += 1
        time.sleep(interval)

    print(f"Sent {packets_sent} packets")


if __name__ == '__main__':
    main()