import p4runtime_sh.shell as sh
import threading
from scapy.all import Ether, IP

sh.setup(
    device_id=0,
    grpc_addr='0.0.0.0:50051',
    election_id=(0, 1), # election stuff
    config=sh.FwdPipeConfig('../../prog/simple_test_with_ctrl/p4info.txt', '../../prog/simple_test_with_ctrl/switch_config.json') # Update this when switching experiments
)

def print_packet(packet):
    eth = Ether(packet.packet.payload)
    if eth.haslayer(IP):
        ip = eth[IP]
        print(f"Ethernet: {eth.summary()}")
        print(f"IP: {ip.summary()}")
    else:
        print(f"Ethernet: {eth.summary()}")

def start_sniffer():
    packet_in = sh.PacketIn()
    try:
        while True:
            packet_in.sniff(function=print_packet, timeout=1)
    except KeyboardInterrupt:
        print("Bye bye")

sniffer_thread = threading.Thread(target=start_sniffer)
sniffer_thread.start()