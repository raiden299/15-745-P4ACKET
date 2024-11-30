import socket
import sys
import time

from scapy.all import IP, Ether, get_if_hwaddr, get_if_list, sendp


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
    pkt = Ether(src=get_if_hwaddr(iface), dst='ff:ff:ff:ff:ff:ff')
    pkt = pkt / IP(dst=addr)

    # Send packets for 30 seconds
    start_time = time.time()
    end_time = start_time + 30
    pkt_size = len(pkt) * 8
    interval = pkt_size / (10 * 1024 * 1024)  # Interval for 10mbps

    while time.time() < end_time:
        sendp(pkt, iface=iface, verbose=False)
        time.sleep(interval)


if __name__ == '__main__':
    main()