import p4runtime-shell.p4runtime_shell as sh

sh.setup(
    device_id=0,
    grpc_addr='0.0.0.0:50051',
    election_id=(0, 1), # election stuff
    config=sh.FwdPipeConfig('../../prog/simple_test_with_ctrl/p4info.txt', '../../prog/simple_test_with_ctrl/switch_config.json') # Update this when switching experiments
)

for msg in sh.PacketIn().sniff():
    print(msg)
