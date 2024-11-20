/* Parts of this code are inspired by the P4 tutorials */

#include <core.p4>
#include <v1model.p4>

/* I'm creating 3 header types for simplicity */

typedef bit<9>  egressSpec_t;
typedef bit<48> macAddr_t;
typedef bit<32> ip4Addr_t;
typedef bit<128> ip6Addr_t;

const bit<16> TYPE_IPV4 = 0x800;
const bit<16> TYPE_IPV6 = 0x86DD;

header ethernet_t {
    macAddr_t dstAddr;
    macAddr_t srcAddr;
    bit<16>   etherType;
}

/* 
    This is the header which will 
    store the bitvector for the tables visited.
    We want it to be between the ethernet layer
    and the ipv4 layer. This header will not exist
    in the incoming packet header, but will be
    inserted at the deparser.
*/
header tcount_t {
    bit<32> tables;
}

header ipv4_t {
    bit<4>    version;
    bit<4>    ihl;
    bit<8>    diffserv;
    bit<16>   totalLen;
    bit<16>   identification;
    bit<3>    flags;
    bit<13>   fragOffset;
    bit<8>    ttl;
    bit<8>    protocol;
    bit<16>   hdrChecksum;
    ip4Addr_t srcAddr;
    ip4Addr_t dstAddr;
}

header ipv6_t {
    bit<4> version;
    bit<8> prio;
    bit<20> flowLabel;
    bit<16> payloadLen;
    bit<8> nxtHdr;
    bit<8> hopLmt;
    ip6Addr_t srcAddr;
    ip6Addr_t dstAddr;
}

struct metadata {
    // Don't need right now
}

struct headers {
    ethernet_t ethernet;
    tcount_t tcount;
    ipv4_t ipv4;
    ipv6_t ipv6;
}

/* A very uninteresting parser */
parser NewParser(packet_in packet, out headers hdr, inout metadata meta, inout standard_metadata_t standard_metadata) {
    state start {
        transition parse_ethernet;
    }

    state parse_ethernet {
        packet.extract(hdr.ethernet);
        transition select(hdr.ethernet.etherType) {
            TYPE_IPV4: parse_ipv4;
            TYPE_IPV6: parse_ipv6;
            default: accept;
        }
    }

    /* tcount not included because we don't expect it in ingress */

    state parse_ipv4 {
        packet.extract(hdr.ipv4);
        transition accept;
    }

    state parse_ipv6 {
        packet.extract(hdr.ipv6);
        transition accept;
    }
}

/* Just there because the model needs it */
control NewVerifyChecksum(inout headers hdr, inout metadata meta) {
    apply {  }
}

control NewIngress(inout headers hdr, inout metadata meta, inout standard_metadata_t standard_metadata) {
    /* Standard drop action */
    action drop() {
        mark_to_drop(standard_metadata);
    }

    /* Set the tables that have been visited */
    action mark_tcount(bit<32> table_pos) {
        hdr.tcount.setValid();
        hdr.tcount.tables = hdr.tcount.tables | table_pos;
    }

    /* Normal IPv4 forwarding stuff */
    action ipv4_forward(macAddr_t dstAddr, egressSpec_t out_port) {
        standard_metadata.egress_spec = out_port; // Set output port
        hdr.ethernet.srcAddr = hdr.ethernet.dstAddr; // Set the source as old dst
        hdr.ethernet.dstAddr = dstAddr; // Set the dst field as new dst
        hdr.ipv4.ttl = hdr.ipv4.ttl - 1;

        mark_tcount(1);
    }

    /* Assuming we use an lpm match for testing purposes */
    table ipv4_lpm {
        key = {
            hdr.ipv4.dstAddr: lpm;
        }

        actions = {
            ipv4_forward;
            drop;
            NoAction;
        }

        size = 1024;
        default_action = drop();
    }

    action ipv6_forward(macAddr_t dstAddr, egressSpec_t out_port) {
        hdr.ipv6.setValid();
        standard_metadata.egress_spec = out_port;
        hdr.ipv6.hopLmt = hdr.ipv6.hopLmt - 1;
        hdr.ethernet.srcAddr = hdr.ethernet.dstAddr;
        hdr.ethernet.dstAddr = dstAddr;

        mark_tcount(3);
    }

    /* Simply forward the ipv6 packet */
    table ipv6_lpm {
        key = {
            hdr.ipv6.dstAddr: lpm;
        }

        actions = {
            ipv6_forward;
            drop;
            NoAction;
        }

        size = 1024;
        default_action = drop();
    }

    action decr_prio() {
        hdr.ipv6.prio = hdr.ipv6.prio - 1;
        mark_tcount(2);
    }

    action incr_prio() {
        hdr.ipv6.prio = hdr.ipv6.prio + 1;
        mark_tcount(2);
    }

    action mult_prio() {
        hdr.ipv6.prio = hdr.ipv6.prio + hdr.ipv6.prio;
        mark_tcount(2);
    }

    /* Check the priority and apply the action accordingly 
        For the purpose of this test p4 program, the following
        is the logic for this table and its associated actions:

        Given a priority (p), if p == 32, we decrement it by 1,
        if p == 64, we increment it by 1, if p == 16, we multiply by 2.
    */
    table ipv6_prio_mark {
        key = {
            hdr.ipv6.prio: exact;
        }

        actions = {
            decr_prio;
            incr_prio;
            mult_prio;
            NoAction;
        }

        size = 32;

        default_action = NoAction();
    }

    /* Actual logic of how packets traverse the tables */
    apply {
        if (hdr.ethernet.isValid()) {
            if (hdr.ethernet.etherType == TYPE_IPV6) {
                ipv6_lpm.apply();
                ipv6_prio_mark.apply();
            } else {
                ipv4_lpm.apply();
            }
        }
    }
}

control NewEgress(inout headers hdr, inout metadata meta, inout standard_metadata_t standard_metadata) {
    apply { }
}

control CalcChecksum(inout headers hdr, inout metadata meta) {
    apply { }
}

control NewDeparser(packet_out packet, in headers hdr) {
    apply {
        packet.emit(hdr.ethernet);
        packet.emit(hdr.ipv4);
        packet.emit(hdr.ipv6);
        packet.emit(hdr.tcount);
    }
}

V1Switch(
    NewParser(),
    NewVerifyChecksum(),
    NewIngress(),
    NewEgress(),
    CalcChecksum(),
    NewDeparser()
) main;

