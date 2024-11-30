.PHONY: all

PROG=prog/simple_test_with_ctrl
SWITCH_EXE=simple_switch_grpc


all:
	p4c --target bmv2 --arch v1model --std p4-16 $(PROG)/switch_config.p4 --p4runtime-files prog/simple_test_with_ctrl/p4info.txt -o $(PROG)
	sudo python3 setup_topology.py --behavioral-exe=$(SWITCH_EXE) --json=$(PROG)/switch_config.json

entries:
	sudo python3 $(PROG)/setup_switch.py

clean:
	sudo mn -c
	rm -r prog/*/*.p4i prog/*/*.json prog/*/*.pcap prog/*/*.txt prog/*/*.sum