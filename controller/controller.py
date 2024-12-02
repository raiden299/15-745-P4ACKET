import p4runtime_sh.shell as sh
import threading
from scapy.all import *
from scapy.packet import Packet
from scapy.fields import ByteField, ShortField, IntField, IPField, StrFixedLenField

# Global packet counter
packet_count = 0

class TCount(Packet):
    name = "TCount"
    fields_desc = []

def process_packet(packet):    
        eth = Ether(packet.packet.payload) # type: ignore
        eth.layers()
        try:
            tcount_raw = bytes(eth.payload)[:4 * num_tables]
            tcount = TCount(tcount_raw)
            tcount.show2()
        except Exception as e:
            print(f"Unidentified packet: {e}")
            return

        global packet_count
        packet_count += 1
        print(f"Packet count: {packet_count}")

def start_sniffer():
    packet_in = sh.PacketIn()
    try:
        while True:
            packet_in.sniff(function=process_packet, timeout=1)
    except KeyboardInterrupt:
        print("Bye bye")

if __name__ == '__main__':
    sh.setup(
        device_id=0,
        grpc_addr='0.0.0.0:50051',
        election_id=(0, 1), # election stuff
        config=sh.FwdPipeConfig('../prog/acl_test/p4info.txt', '../prog/acl_test/switch_config.json') # Update this when switching experiments
    )

    # Prepare info required for analysis
    p4info = sh.context.p4info
    table_aliases = [table.preamble.alias for table in p4info.tables]
    table_action_refs = {table.preamble.alias: [ref.id for ref in table.action_refs] for table in p4info.tables}
    actions = {action.preamble.id: action.preamble.alias for action in p4info.actions}
    table_actions = {alias: [actions[ref] for ref in refs] for alias, refs in table_action_refs.items()}

    num_tables = len(table_aliases)

    # Populate the field descriptors in the packet
    TCount.fields_desc = [
        BitField(table_alias, 0, 32) for table_alias in table_aliases
    ]

    print("Table Aliases:", table_aliases)
    print("Table Action References:", table_action_refs)
    print("Table Actions:", table_actions)

    sniffer_thread = threading.Thread(target=start_sniffer)
    sniffer_thread.start()

