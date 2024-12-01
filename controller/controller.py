import p4runtime_sh.shell as sh
import threading
from scapy.all import *
import struct

# Define a custom Scapy layer for the TCount header
class TCount(Packet):
    name = "TCount"
    fields_desc = [
        BitField("ipv4_lpm", 0, 32),
        BitField("udp_acl", 0, 32),
        BitField("dhcp_acl", 0, 32)
    ]

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

# Extend Scapy's bind_layers to recognize the custom header
def bind_tcount_layer():
    sh.setup(
        device_id=0,
        grpc_addr='0.0.0.0:50051',
        election_id=(0, 1),
        config=sh.FwdPipeConfig('../../prog/acl_test/p4info.txt', '../../prog/acl_test/switch_config.json')
    )
    # Bind TCount layer to DHCP
    bind_layers(UDP, DHCP)
    bind_layers(DHCP, TCount)

def print_packet(packet):
    try:
        # Convert the raw packet to an Ethernet frame
        #eth = Ether(packet.packet.payload)
        tcount = TCount(packet.packet.payload)
        tcount.show2()
        print("Packet Received:")
        print("Ethernet layer")
        #eth.show2()
        
        # Check for IP layer
        if IP in eth:
            print("\nIP layer")
            #eth[IP].show2()
            
            # Check for UDP layer
            if UDP in eth:
                print("\nUDP layer")
                #eth[UDP].show2()
                #eth[BOOTP].show2()
                #print("Now printing the options\n")
                #print(eth[BOOTP].options)
                bootp_raw = bytes(eth[BOOTP])
                custom_dhcp = DHCP(bootp_raw)
                custom_dhcp.show2()
                # # Check for custom DHCP layer
                # udp_payload = eth[UDP].payload
                # if isinstance(udp_payload, Raw):
                #     try:
                #         dhcp_packet = DHCP(udp_payload)
                #         if dhcp_packet.magic_cookie == 0x63825363:  # DHCP magic cookie
                #             print("\nDHCP layer")
                #             dhcp_packet.show2()
                            
                #             # Check for TCount layer
                #             if TCount in dhcp_packet:
                #                 print("\nTCount layer")
                #                 dhcp_packet[TCount].show2()
                #             else:
                #                 print("\nTCount layer not found")
                #         else:
                #             print("\nDHCP layer not found")
                #     except:
                #         print("\nFailed to parse DHCP layer")
                # else:
                #     print("\nDHCP layer not found")
            else:
                print("\nUDP layer not found")
        else:
            print("\nIP layer not found")
        
    except Exception as e:
        print(f"Error parsing packet: {e}")
        # Optional: print more debug information
        print(f"Packet object type: {type(packet)}")
        print(f"Packet attributes: {dir(packet)}")


def start_sniffer():
    # Bind custom layers before starting sniffer
    bind_tcount_layer()
    
    packet_in = sh.PacketIn()
    try:
        while True:
            packet_in.sniff(function=print_packet, timeout=1)
    except KeyboardInterrupt:
        print("Sniffer stopped.")

# Start sniffer in a separate thread
sniffer_thread = threading.Thread(target=start_sniffer)
sniffer_thread.start()

# Keep main thread running
try:
    sniffer_thread.join()
except KeyboardInterrupt:
    print("Exiting...")
