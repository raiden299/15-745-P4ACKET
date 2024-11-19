import subprocess
import json

def run_command(command):
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    if process.returncode != 0:
        print(f"Error running command: {command}\n{stderr.decode('utf-8')}")
    return stdout.decode('utf-8')

def setup_switch(switch_name, thrift_port, table_entries):
    for entry in table_entries:
        command = f"echo '{entry}' | simple_switch_CLI --thrift-port {thrift_port}"
        run_command(command)
        print(f"Set up entry on {switch_name}: {entry}")

def main():
    with open('setup_config.json', 'r') as f:
        config = json.load(f)

    table_entries_s1 = [
        "table_add ipv4_lpm ipv4_forward 10.0.1.1/32 => 08:00:00:00:01:11 1",
        "table_add ipv4_lpm ipv4_forward 10.0.2.2/32 => 08:00:00:00:02:00 2"
    ]

    table_entries_s2 = [
        "table_add ipv4_lpm ipv4_forward 10.0.1.1/32 => 08:00:00:00:01:00 1",
        "table_add ipv4_lpm ipv4_forward 10.0.2.2/32 => 08:00:00:00:02:22 2"
    ]

    setup_switch('s1', 9090, table_entries_s1)
    setup_switch('s2', 9091, table_entries_s2)

if __name__ == '__main__':
    main()