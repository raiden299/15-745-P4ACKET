#!/usr/bin/env python3
import os
import sys

from scapy.all import (
    Packet,
    TCP,
    FieldLenField,
    FieldListField,
    IntField,
    IPOption,
    ShortField,
    get_if_list,
    sniff,
    BitField
)
from scapy.layers.inet import _IPOption_HDR

class tcount(Packet):
    name = "tcount"
    fields_desc = [
        BitField("ipv4_lpm", 0, 32),
        BitField("udp_acl", 0, 32),
        BitField("dhcp_acl", 0, 32)
    ]

def get_if():
    ifs=get_if_list()
    iface=None
    for i in get_if_list():
        if "eth0" in i:
            iface=i
            break;
    if not iface:
        print("Cannot find eth0 interface")
        exit(1)
    return iface

class IPOption_MRI(IPOption):
    name = "MRI"
    option = 31
    fields_desc = [ _IPOption_HDR,
                    FieldLenField("length", None, fmt="B",
                                  length_of="swids",
                                  adjust=lambda pkt,l:l+4),
                    ShortField("count", 0),
                    FieldListField("swids",
                                   [],
                                   IntField("", 0),
                                   length_from=lambda pkt:pkt.count*4) ]
def handle_pkt(pkt):
    # if TCP in pkt and pkt[TCP].dport == 1234:
    #     print("got a packet")
    # tc = pkt[tcount]
    # print("\nTCount Layer Details:")
    # print(f"IPv4 LPM: {tc.ipv4_lpm}")
    # print(f"UDP ACL:  {tc.udp_acl}")
    # print(f"DHCP ACL: {tc.dhcp_acl}")
    print("Layers in the packet:")
    current_layer = pkt
    while current_layer:
        print(current_layer.name)
        current_layer = current_layer.payload

    pkt.show2()
    #    hexdump(pkt)
    sys.stdout.flush()


def main():
    ifaces = [i for i in os.listdir('/sys/class/net/') if 'eth' in i]
    iface = ifaces[0]
    print("sniffing on %s" % iface)
    sys.stdout.flush()
    sniff(iface = iface,
          prn = lambda x: handle_pkt(x))

if __name__ == '__main__':
    main()
