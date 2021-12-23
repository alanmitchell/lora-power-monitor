#!/usr/bin/env python3

from secrets import token_hex
from pathlib import Path
import time
from serial import Serial

APP_EUI = '0000000000000001'

FN_KEYS = 'keys.csv'
if not Path(FN_KEYS).exists():
    # start the file with a header row
    with open(FN_KEYS, 'w') as fkeys:
        fkeys.write('dev_eui,app_eui,app_key\n')

# Generate an App Key
app_key = token_hex(16).upper()

cmds = (
    'FDEFAULT',
    'UART=TIMEOUT, 2000',
    f'ID=APPEUI, "{APP_EUI}"',
    f'KEY=APPKEY,"{app_key}"',
    'MODE=LWOTAA',
    'DR=US915HYBRID',
    'CH=NUM,8-15',
    'CLASS=A',
    'ADR=OFF',
    'DR=1',
    'DELAY=RX1,5000',
    'DELAY=RX2,6000',
    'JOIN=AUTO,10,1200,0',
)
try:
    p = Serial('/dev/ttyUSB0', timeout=1.0)

    # determine the Dev EUI of the device
    p.write(b'AT+ID=DEVEUI\n')
    resp = p.readline()
    dev_eui = resp.decode('utf-8').strip().split(' ')[-1].replace(':','')

    for cmd in cmds:
        print('\n' + cmd)
        cmd_full = f'AT+{cmd}\n'.encode('utf-8')
        p.write(cmd_full)
        resp = p.readlines()
        for lin in resp:
            print(lin.decode('utf-8').strip())

except Exception as e:
    raise e

finally:
    p.close()
    with open(FN_KEYS, 'a') as fkeys:
        fkeys.write(f'{dev_eui},{APP_EUI},{app_key}\n')
