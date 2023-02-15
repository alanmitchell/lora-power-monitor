#!/usr/bin/env python

"""Reads voltage values from the SCPI Multimeter, calculates power based on a 
known resistive load, and then compares to the power readings spooled from the
LoRa Power monitor.

Add the "-w" command line switch to have the script write a new calibrate.py file
on the microcontroller.

The V-squared / R may be scaled up by a Turns
multiplier, which makes it easier to compare to a power measured with current
being sensed through mulitple passes of wire.

Adjust the config_calib.py file as needed. 
"""

from time import time
from serial import Serial
import argparse

import config_calib as config


parser = argparse.ArgumentParser()
parser.add_argument(
    "-w", 
    "--write", 
    dest='write',
    action='store_true',
    help="Causes new Calibration constant to be written to Microcontroller."
    )
parser.set_defaults(write=False)

args = parser.parse_args()

v2_tot = 0.0
n = 0
port_volt = Serial(config.PORT_VOLT, 115200, timeout=1.0)

pwr_tot = 0.0
port_pwr = Serial(config.PORT_PWR, 115200, timeout=2.0)

while n < config.TOTAL_READS:

    lin_pwr = port_pwr.readline()
    try:
        lin_pwr = lin_pwr.decode('utf-8').strip()
    except:
        lin_pwr = ''
    if lin_pwr.startswith('val') and len(lin_pwr.split(' '))==3:
        _, pwr, calib_mult = lin_pwr.split(' ')
        pwr = float(pwr)
        calib_mult = float(calib_mult)

        # read the voltage
        port_volt.write('meas1?\n'.encode('utf-8'))
        volts = port_volt.readline().decode('utf-8').strip()
        volts = float(volts)
        
        if volts >= config.V_MIN and volts <= config.V_MAX:
            v2_tot += volts * volts
            pwr_tot += pwr
            n += 1
            print(f'lora: {pwr / config.TURNS:.2f}    actual: {volts*volts/config.LOAD_R:.2f}')

v2_avg = v2_tot / n
pwr_actual_avg = v2_avg / config.LOAD_R
pwr_lora_avg = pwr_tot / config.TURNS / n
calib_adj = pwr_actual_avg / pwr_lora_avg
new_calib_mult = int(calib_mult * calib_adj)

print(f'\nAverages: lora: {pwr_lora_avg:.2f}    actual: {pwr_actual_avg:.2f}')
print(f'Error: {(pwr_lora_avg - pwr_actual_avg)/pwr_actual_avg * 100:.2f}%')
print(f'New Calibration Multiplier: {new_calib_mult}')

if args.write:
    s = f'CALIB_MULT = {new_calib_mult}\n'
    with open('/media/alan/CIRCUITPY/calibrate.py', 'w') as fout:
        fout.write(s)
    print('New Calibration multiplier was written to Microcontroller!')
