#!/usr/bin/env python

"""Script to Calibrate LoRa Power Monitors.
"""

from time import time
import sys
from pathlib import Path

import serial.tools.list_ports
from serial import Serial
from questionary import confirm

from pzem import read_power

def path_to_calibrate_file():
    if sys.platform.startswith('lin'):
        return Path("/media/alan/CIRCUITPY/calibrate.py")
    elif sys.platform.startswith('win'):
        for drive in ("D", "E", "F", "G"):
            p = Path(f"{drive}:\\calibrate.py")
            if p.exists():
                return p
    return None

# Find all serial ports on the machine.
all_ports = serial.tools.list_ports.comports()

# Find the serial port of the actual power measuring device (probabaly
# a PZEM-004T device).
port_actual_name = None
for p in all_ports:
    if 'CP21' in p.description:
        port_actual_name = p.device
        break
if port_actual_name is None:
    print("ERROR: Serial port for PZEM Actual Power Measurement not found. Press Enter to Exit...")
    input()
    sys.exit()
else:
    print(f"\nFound the Actual Power Measurement device on port {port_actual_name}")

# Bring the configuration variables into the namespace. I'm doing it this way
# So that the config file will stay outside of the one-file pyinstaller executable.
# This brings in the TOTAL_READS, TURNS, ACTUAL_CALIB_MULT and CONFIG_PATH
# constants used by this script.
exec(open("config.py").read())

do_again = True
while do_again:

    input("\nConnect the LoRa Power Monitor and press Enter to Continue...")

    # Find the serial port of the LoRa Power Monitor
    port_lora_name = None
    for p in all_ports:
        if sys.platform.startswith('win') and p.description.startswith("USB Serial Device"):
            port_lora_name = p.device
            break
        elif sys.platform.startswith('lin') and 'QT Py' in p.description:
            port_lora_name = p.device
            break
    if port_lora_name is None:
        print("ERROR: Serial port LoRa Power Monitor not found. Press Enter to Exit...")
        input()
        sys.exit()
    else:
        print(f"\nFound the LoRa Power Monitor on port {port_lora_name}\n")

    with Serial(port_lora_name, 115200, timeout=2.0) as port_lora:

        n = 0
        actual_pwr_tot = 0.0
        lora_pwr_tot = 0.0

        while n < TOTAL_READS:

            # read a line from the LoRa power monitor
            lin_lora = port_lora.readline()
            try:
                lin_lora = lin_lora.decode('utf-8').strip()
            except:
                lin_lora = ''

            if lin_lora.startswith('val') and len(lin_lora.split(' '))==3:
                _, lora_pwr, calib_mult = lin_lora.split(' ')
                lora_pwr = float(lora_pwr)
                calib_mult = float(calib_mult)

                # read the power from the actual power measuring device
                actual_pwr = read_power(port_actual_name, ACTUAL_CALIB_MULT)
                if actual_pwr is not None:
                    lora_pwr_tot += lora_pwr
                    actual_pwr_tot += actual_pwr
                    n += 1
                    print(f'lora: {lora_pwr / TURNS:.2f}    actual: {actual_pwr:.2f}')

    actual_pwr_avg = actual_pwr_tot / n
    lora_pwr_avg = lora_pwr_tot / TURNS / n
    calib_adj = actual_pwr_avg / lora_pwr_avg
    new_calib_mult = int(calib_mult * calib_adj)

    print(f'\nAverages: lora: {lora_pwr_avg:.2f}    actual: {actual_pwr_avg:.2f}')
    print(f'Error: {(lora_pwr_avg - actual_pwr_avg)/actual_pwr_avg * 100:.2f}%')
    print(f'New Calibration Multiplier: {new_calib_mult}')
    print()

    write_calib_file = confirm("Do you want to store the new Calibration Constant to the LoRa Power Monitor?").ask()
    if write_calib_file:
        s = f'CALIB_MULT = {new_calib_mult}\n'
        calib_path = path_to_calibrate_file()
        if calib_path:
            with open(calib_path, 'w') as fout:
                fout.write(s)
            print('New Calibration multiplier was written to the Power Monitor!')
            print()
        else:
            print("calibrate.py file was not found")

    do_again = confirm("Do you want to calibrate another LoRa Power Monitor").ask()
