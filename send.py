import socket
import sys
import time

from scapy.all import IP, Ether, UDP, get_if_hwaddr, get_if_list, sendp
from scapy.packet import Packet
from scapy.fields import ByteField, ShortField, IntField, IPField, StrFixedLenField


class DHCP(Packet):
    name = "DHCP"
    fields_desc = [
        ByteField("op", 1),
        ByteField("htype", 1),
        ByteField("hlen", 6),
        ByteField("hops", 0),
        IntField("xid", 0),
        ShortField("secs", 0),
        ShortField("flags", 0),
        IPField("ciaddr", "0.0.0.0"),
        IPField("yiaddr", "0.0.0.0"),
        IPField("siaddr", "0.0.0.0"),
        IPField("giaddr", "0.0.0.0"),
        StrFixedLenField("chaddr", b'\x00' * 16, length=16),
        StrFixedLenField("sname", b'\x00' * 64, length=64),
        StrFixedLenField("file", b'\x00' * 128, length=128),
        IntField("magic_cookie", 0x63825363)
    ]


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
    pkt = pkt / IP(dst=dst_addr) / UDP(dport=dst_port)
    return pkt


def create_dhcp_packet():
    pkt = Ether(src=get_if_hwaddr(get_if()), dst='ff:ff:ff:ff:ff:ff')
    pkt = pkt / IP(src='0.0.0.0', dst='255.255.255.255') / UDP(sport=68, dport=67) / DHCP()
    return pkt


def main():

    if len(sys.argv) < 2:
        print('pass 2 arguments: <destination> "<message>"')
        exit(1)

    addr = socket.gethostbyname(sys.argv[1])
    iface = get_if()

    print("sending on interface %s to %s" % (iface, str(addr)))

    # pkt = create_ipv4_packet(addr)
    # pkt = create_udp_packet(addr, 12345)
    pkt = create_dhcp_packet()

    # Send packets at 10Mbps for 30 seconds
    start_time = time.time()
    end_time = start_time + 30
    pkt_size = len(pkt) * 8
    interval = pkt_size / (10 * 1024 * 1024)

    while time.time() < end_time:
        sendp(pkt, iface=iface, verbose=False)
        time.sleep(interval)


if __name__ == '__main__':
    main()