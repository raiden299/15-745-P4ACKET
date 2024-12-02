import socket
import sys
import time

from scapy.all import *
from scapy.packet import Packet
from scapy.fields import ByteField, ShortField, IntField, IPField, StrFixedLenField, ShortEnumField, XShortField
import random

########### EXPERIMENT PARAMS ###########
DURATION_S = 300

########### SEND FUNCTIONS ###########

## IPv4 packets

def create_ipv4_block_packet(dst_addr):
    pkt = Ether(src=get_if_hwaddr(get_if()), dst='ff:ff:ff:ff:ff:ff')
    pkt = pkt / IP(dst='0.0.0.0')
    return pkt

def create_ipv4_regular_packet(dst_addr):
    pkt = Ether(src=get_if_hwaddr(get_if()), dst='ff:ff:ff:ff:ff:ff')
    pkt = pkt / IP(dst=dst_addr)
    return pkt

## UDP Packets

def create_udp_block_packet(dst_addr, dst_port):
    pkt = Ether(src=get_if_hwaddr(get_if()), dst='ff:ff:ff:ff:ff:ff')
    pkt = pkt / IP(dst=dst_addr) / UDP(sport=12345, dport=dst_port)
    return pkt

def create_udp_regular_packet(dst_addr, dst_port):
    pkt = Ether(src=get_if_hwaddr(get_if()), dst='ff:ff:ff:ff:ff:ff')
    pkt = pkt / IP(dst=dst_addr) / UDP(sport=22346, dport=dst_port)
    return pkt

## DHCP Packets

def create_dhcp_block_packet(dst_addr):
    pkt = Ether(src=get_if_hwaddr(get_if()), dst='ff:ff:ff:ff:ff:ff')
    pkt = pkt / IP(src='10.0.0.10', dst=dst_addr, proto=17) / UDP(sport=67, dport=68) / BOOTP(ciaddr='10.0.0.10')
    return pkt

def create_dhcp_regular_packet(dst_addr):
    pkt = Ether(src=get_if_hwaddr(get_if()), dst='ff:ff:ff:ff:ff:ff')
    pkt = pkt / IP(src='10.0.0.10', dst=dst_addr, proto=17) / UDP(sport=67, dport=68) / BOOTP(ciaddr='10.40.0.10')
    return pkt

########### UTIL FUNCTIONS ###########

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


def main():

    if len(sys.argv) < 2:
        print('pass 2 arguments: <destination> "<message>"')
        exit(1)

    addr = socket.gethostbyname(sys.argv[1])
    iface = get_if()

    print("sending on interface %s to %s" % (iface, str(addr)))

    # Add any new functions to this list and update packet_args
    packet_functions = [create_ipv4_regular_packet, create_ipv4_block_packet, create_udp_regular_packet, create_udp_block_packet, create_dhcp_regular_packet, create_dhcp_block_packet]
    packet_args = {
        create_ipv4_regular_packet: [addr],
        create_ipv4_block_packet: [addr],
        create_udp_regular_packet: [addr, 80],
        create_udp_block_packet: [addr, 80],
        create_dhcp_regular_packet: [addr],
        create_dhcp_block_packet: [addr]
    }

    # I think could be faster but is okay for now
    def get_random_packet(addr):
        rand__func = random.randint(0, len(packet_functions)-1)
        return packet_functions[rand__func](*packet_args[packet_functions[rand__func]])

    # Send packets for 30 seconds
    end_time = time.time() + DURATION_S
    packets_sent = 0

    while time.time() < end_time:
        pkt = get_random_packet(addr)
        sendp(pkt, iface=iface, verbose=False)
        packets_sent += 1

    print(f"Sent {packets_sent} packets")


if __name__ == '__main__':
    main()