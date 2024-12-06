# 15-745-P4CKET
Mininet setup:

1) Update the Makefile with the program you want to run (programs found in prog/)
2) Update topology config (setup_config.json)
3) Run the setup (`make`)
4) Move `controller/controller.py` into `controller/p4runtime-shell/`.
5) Start the controller (`python3 p4runtime-shell/controller.py`)
6) In a separate terminal, update table entries (prog/<prog_name>/setup_switch.py) by calling `make entries`

In November 2024, the Tofino backend for p4c was open-sourced. We use it to get the stages allocated to each table.

You will want to compile `p4c/` from source first. To include the Tofino backend, you must ensure that the ENABLE_TOFINO flag in the `CMakeLists.txt` is set to `ON`.

To generate a report for the tofino target for v1model, use a command similar to this:

```
./p4c-barefoot --target tofino2 --arch v1model  --display-power-budget --p4runtime-format json --create-graphs  sample.p4
```