#!/usr/bin/env python3

# If you don't have perf installed, install it with:
# sudo apt install linux-tools-common linux-tools-generic linux-tools-`uname -r`

# To enable perf usage without sudo, run:
# echo -1 | sudo tee /proc/sys/kernel/perf_event_paranoid
# This configuration will be reset if you reboot your pc,
# to make it permanent you need to edit /etc/sysctl.conf

import subprocess, string, multiprocessing

def run_single(flag):
    output = subprocess.run(['./totem1-uploadme'],
        input=flag.encode(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE).stdout

    # print(flag, output)
    return 'Correct! You found the flag!' in output.decode()


flag = ''
for i in range(100):
    found, best = 'x', 0
    for ch in string.printable:
        if ch in "\n\r\t": continue
        instructions = run_single(flag + ch)
        # print(ch, instructions)
        if instructions:
            best = instructions
            found = ch
    flag += found
    print(flag)
    if flag[-1] == '}':
        break

# flag{d0nt_Th1nk-0f-3l3ph4ntz}
