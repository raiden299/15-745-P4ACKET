#include <core.p4>
#include <v1model.p4>

// Header definitions
header ethernet_t {
    bit<48> dstAddr;
    bit<48> srcAddr;
    bit<16> etherType;
}

header ipv4_h {
    bit<4>  version;
    bit<4>  ihl;
    bit<8>  diffserv;
    bit<16> totalLen;
    bit<16> identification;
    bit<3>  flags;
    bit<13> fragOffset;
    bit<8>  ttl;
    bit<8>  protocol;
    bit<16> hdrChecksum;
    bit<32> srcAddr;
    bit<32> dstAddr;
}

header udp_h {
    bit<16> srcPort;
    bit<16> dstPort;
    bit<16> length;
    bit<16> checksum;
}

header dhcp_h {
    bit<8>  op;           
    bit<8>  htype;        
    bit<8>  hlen;         
    bit<8>  hops;         
    bit<32> xid;          
    bit<16> secs;         
    bit<16> flags;        
    bit<32> ciaddr;       
    bit<32> yiaddr;       
    bit<32> siaddr;        
    bit<32> giaddr;       
    bit<128> chaddr;      
    bit<512> sname;       
    bit<1024> file;       
}

header __tcount_t {
    bit<32> ipv4_lpm;
    bit<32> udp_acl;
    bit<32> dhcp_acl; 
}

// Register to count number of packets
register<bit<48>>(1) __packet_count;

// Header stack
struct headers {
    ethernet_t ethernet;
    ipv4_h ipv4;
    udp_h udp;
    dhcp_h dhcp;
    __tcount_t __tcount;
}

// Metadata structure
struct metadata {
    bool ipv4_valid;
    bool udp_valid;
    bool dhcp_valid;
    @field_list(1)
    bit<32> __ipv4_lpm;
    @field_list(1)
    bit<32> __udp_acl;
    @field_list(1)
    bit<32> __dhcp_acl;
}

// Parser
parser MyParser(packet_in packet,
                out headers hdr,
                inout metadata meta,
                inout standard_metadata_t standard_meta) {
    
    state start {
        transition parse_ethernet;
    }

    state parse_ethernet {
        packet.extract(hdr.ethernet);
        transition select(hdr.ethernet.etherType) {
            0x0800: parse_ipv4;
            default: accept;
        }
    }

    state parse_ipv4 {
        packet.extract(hdr.ipv4);
        meta.ipv4_valid = true;
        transition select(hdr.ipv4.protocol) {
            17: parse_udp;
            default: accept;
        }
    }

    state parse_udp {
        packet.extract(hdr.udp);
        meta.udp_valid = true;
        transition select(hdr.udp.srcPort) {
            67: parse_dhcp;
            default: accept;
        }
    }

    state parse_dhcp {
        packet.extract(hdr.dhcp);
        meta.dhcp_valid = true;
        transition accept;
    }
}

// Unified Ingress Control Block
control ACLIngress(inout headers hdr,
                  inout metadata meta,
                  inout standard_metadata_t standard_metadata) {
    
    action drop_ipv4() {
        meta.__ipv4_lpm = meta.__ipv4_lpm | 2;
        mark_to_drop(standard_metadata);
    }

    action __clone_to_controller() {
        clone_preserving_field_list(CloneType.I2E, 100, 1);
    }

    action ipv4_forward(bit<48> dstAddr, bit<9> port) {
        meta.__ipv4_lpm = meta.__ipv4_lpm | 1;
        standard_metadata.egress_spec = port;
        hdr.ethernet.srcAddr = hdr.ethernet.dstAddr;
        hdr.ethernet.dstAddr = dstAddr;
        hdr.ipv4.ttl = hdr.ipv4.ttl - 1;
    }

    table ipv4_lpm {
        key = {
            hdr.ipv4.dstAddr: lpm;
        }
        actions = {
            ipv4_forward;
            drop_ipv4;
            NoAction;
        }
        size = 1024;
        default_action = drop_ipv4();
    }

    action drop_udp() {
        meta.__udp_acl = meta.__udp_acl | 1;
        mark_to_drop(standard_metadata);
    }

    // UDP ACL Table
    table udp_acl {
        key = {
            hdr.udp.srcPort: exact;
            hdr.udp.dstPort: exact;
        }
        actions = {
            drop_udp;
            NoAction;
        }
        size = 1024;
        default_action = NoAction();
    }

    action drop_dhcp() {
        meta.__dhcp_acl = meta.__dhcp_acl | 1;
        mark_to_drop(standard_metadata);
    }

    // DHCP ACL Table
    table dhcp_acl {
        key = {
            hdr.dhcp.ciaddr: exact;
        }
        actions = {
            drop_dhcp;
            NoAction;
        }
        size = 1024;
        default_action = NoAction();
    }

    apply {
        // Conditional processing based on packet validity
        bit<48> __count;
        bit<32> __idx = 0;
        __packet_count.read(__count, __idx);
        __count = __count + 1;
        __packet_count.write(__idx, __count);
        if (meta.ipv4_valid) {
            ipv4_lpm.apply();
            
            if (meta.udp_valid) {
                udp_acl.apply();
                
                if (meta.dhcp_valid) {
                    dhcp_acl.apply();
                }
            }
        }

        if (__count & 127 == 0) {
            __clone_to_controller();
        }
    }
}

control ACLEgress(inout headers hdr,
                  inout metadata meta,
                  inout standard_metadata_t standard_meta) {
    apply{
        // Check if the packet is a clone
        if (standard_meta.instance_type == 1) {
            hdr.__tcount.setValid();
            hdr.__tcount.ipv4_lpm = meta.__ipv4_lpm;
            hdr.__tcount.udp_acl = meta.__udp_acl;
            hdr.__tcount.dhcp_acl = meta.__dhcp_acl;
        }
        
    }
    
}

// Deparser
control MyDeparser(packet_out packet, in headers hdr) {
    apply {
        packet.emit(hdr.ethernet);
        packet.emit(hdr.__tcount);
        packet.emit(hdr.ipv4);
        packet.emit(hdr.udp);
        packet.emit(hdr.dhcp);
    }
}

// Checksum verification
control MyVerifyChecksum(inout headers hdr, inout metadata meta) {
    apply { }
}

// Checksum computation
control MyComputeChecksum(inout headers hdr, inout metadata meta) {
    apply {
        update_checksum(
        hdr.ipv4.isValid(),
            { hdr.ipv4.version,
              hdr.ipv4.ihl,
              hdr.ipv4.diffserv,
              hdr.ipv4.totalLen,
              hdr.ipv4.identification,
              hdr.ipv4.flags,
              hdr.ipv4.fragOffset,
              hdr.ipv4.ttl,
              hdr.ipv4.protocol,
              hdr.ipv4.srcAddr,
              hdr.ipv4.dstAddr },
            hdr.ipv4.hdrChecksum,
            HashAlgorithm.csum16);
    }
}

// Switch definition for BMv2
V1Switch(
    MyParser(),
    MyVerifyChecksum(),
    ACLIngress(),
    ACLEgress(),
    MyComputeChecksum(),
    MyDeparser()
) main;