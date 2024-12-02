# 15-745-P4CKET
Mininet setup:

1) Update the Makefile with the program you want to run (programs found in prog/)
2) Update topology config (setup_config.json)
3) Run the setup (`make`)
4) Move `controller/controller.py` into `controller/p4runtime-shell/`.
5) Start the controller (`python3 p4runtime-shell/controller.py`)
6) In a separate terminal, update table entries (prog/<prog_name>/setup_switch.py) by calling `make entries`