#!/usr/bin/python

from mininet.net import Mininet
from mininet.node import Controller, RemoteController
from mininet.node import CPULimitedHost, Host, Node
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink, Intf
import json, argparse

from p4_mininet import P4Switch, P4Host

parser = argparse.ArgumentParser(description='Mininet demo')
parser.add_argument('--behavioral-exe', help='Path to behavioral executable',
                    type=str, action="store", required=True)
parser.add_argument('--thrift-port', help='Thrift server port for table updates',
                    type=int, action="store", default=9090)
parser.add_argument('--num-hosts', help='Number of hosts to connect to switch',
                    type=int, action="store", default=2)
parser.add_argument('--mode', choices=['l2', 'l3'], type=str, default='l3')
parser.add_argument('--json', help='Path to JSON config file',
                    type=str, action="store", required=True)
parser.add_argument('--log-file', help='Path to write the switch log file',
                    type=str, action="store", required=False)
parser.add_argument('--pcap-dump', help='Dump packets on interfaces to pcap files',
                    type=str, action="store", required=False, default=False)
parser.add_argument('--switch-config', help='simple_switch_CLI script to configure switch',
                    type=str, action="store", required=False, default=False)
parser.add_argument('--cli-message', help='Message to print before starting CLI',
                    type=str, action="store", required=False, default=False)

args = parser.parse_args()

def load_config(config_file):
    with open(config_file, 'r') as f:
        return json.load(f)

def setup_topology(config):
    net = Mininet(controller=None, link=TCLink, switch=P4Switch, host=P4Host)
    
    hosts = {}
    switches = {}
    
    for host in config.get('hosts', []):
        h = net.addHost(
            host['name'],
            ip=host.get('ip'),
            mac=host.get('mac'),
        )
        hosts[host['name']] = h
        if 'commands' in host:
            for cmd in host['commands']:
                h.cmd(cmd)
        
    for switch in config.get('switches', []):
        s = net.addSwitch(
            switch['name'],
            sw_path=args.behavioral_exe,
            json_path=args.json,
            thrift_port=switch['thrift_port'],
            log_console=True,
            log_file=args.log_file,
            pcap_dump=args.pcap_dump,
            enable_debugger=False,
        )
        switches[switch['name']] = s
        
    for link in config.get('links', []):
        node1 = hosts.get(link['node1']) or switches.get(link['node1'])
        node2 = hosts.get(link['node2']) or switches.get(link['node2'])
        
        if node1 and node2:
            net.addLink(
                node1,
                node2,
                delay=link.get('delay', '0ms'),
                bw=link.get('bandwidth'),
                loss=link.get('loss', 0),
                max_queue_size=link.get('max_queue_size', 1000)
            )
    
    return net

def start_network(net):
    net.start()

def stop_network(net):
    net.stop()

def start_cli(net):
    CLI(net)

def configure_hosts(net, config):
    for host in config.get('hosts', []):
        if 'commands' in host:
            h = net.get(host['name'])
            for cmd in host['commands']:
                h.cmd(cmd)

if __name__ == '__main__':
    setLogLevel('info')
    
    config = load_config('setup_config.json')
    net = setup_topology(config)
    start_network(net)
    configure_hosts(net, config)
    start_cli(net)
    stop_network(net)