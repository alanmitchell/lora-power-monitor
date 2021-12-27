#!/usr/bin/env python3

port = '/dev/ttyUSB0'

import time
from serial import Serial

with Serial(port, timeout=0) as p:

    n = 0
    while True:
        n += 1
        if n % 10 == 0:
            hexstr = f'{n:X}'
            #if len(hexstr) % 2 != 0:
            #    hexstr = '0' + hexstr
            # Discovered that the 0 padding is not needed
            cmd = f'AT+MSGHEX="{hexstr}"\n'
            print(cmd)
            p.write(cmd.encode('utf-8'))

        while True:
            lin = p.readline()
            if lin:
                print(lin)
            else:
                break

        time.sleep(1.0)
