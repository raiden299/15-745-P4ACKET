import p4runtime_sh.shell as sh
import threading
from scapy.all import *
from scapy.packet import Packet
from scapy.fields import ByteField, ShortField, IntField, IPField, StrFixedLenField

# Global variables
packet_count = 0
bitvec_arr = []
adjacency_list = {}

class TCount(Packet):
    name = "TCount"
    fields_desc = []

def print_adjacency_list():
    for field, adj_fields in adjacency_list.items():
        print(f"{field} -> {adj_fields}")

def print_adjacency_list_text():
    print(f"---- Interference list ----")
    for table, dependencies in adjacency_list.items():
        print(f"Table {table} interferes with: {' '.join(dependencies)}")

def calc_per_table_hit_rate():
    for i, bitvec in enumerate(bitvec_arr):
        hit_percentage = (sum(bitvec) / packet_count) * 100
        print(f"Table {TCount.fields_desc[i].name} hit percentage: {hit_percentage}%")

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
        
        global bitvec_arr, packet_count, adjacency_list
        local_bitvec_arr = []
        for field in TCount.fields_desc:
            bitvec = [(tcount.getfieldval(field.name) >> i) & 1 for i in range(31, -1, -1)]
            local_bitvec_arr.append(bitvec)

        if len(bitvec_arr) == 0:
            bitvec_arr = local_bitvec_arr
        else:
            # Do an element-wise sum of each element in the bitvec_arr with the local_bitvec_arr
            bitvec_arr = [list(map(lambda x, y: x + y, bitvec_arr[i], local_bitvec_arr[i])) for i in range(len(bitvec_arr))]

        for i, field in enumerate(tcount.fields_desc):
            if field.name not in adjacency_list:
                adjacency_list[field.name] = []
            for j in range(i + 1, len(tcount.fields_desc)):
                if tcount.fields_desc[j].name not in adjacency_list:
                    adjacency_list[tcount.fields_desc[j].name] = []
                if tcount.getfieldval(field.name) > 0 and tcount.getfieldval(tcount.fields_desc[j].name) > 0:
                    if tcount.fields_desc[j].name not in adjacency_list[field.name]:
                        adjacency_list[field.name].append(tcount.fields_desc[j].name)
                        adjacency_list[tcount.fields_desc[j].name].append(field.name)

        packet_count += 1

        if packet_count % 10 == 0:
            calc_per_table_hit_rate()
            print_adjacency_list()
            print_adjacency_list_text()

        print(f"Packet count: {packet_count}")
        print(bitvec_arr)

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

