"""CircuitPython code to measure electrical power and transmit data via LoRaWAN.
The radio module used is a SEEED Studio Grove E5. Voltage is sampled from an 
Jameco 5VAC power adapter and current sampled from a CR Magnetics CR 3110-3000 CT.
Both current and voltage waveforms are connected to a 2.048 Volt reference voltage 
so that the AC voltage swing stays within limits of the microcontroller ADC.
"""
import time
import board
import busio
import sys
import gc

from detail_power_reader import DetailReader
from average_power_reader import AverageReader
import lora
from config import config

# disable garbage collector but manually collect prior to and after
# power measurement.
gc.disable()

# Serial port talking to LoRaWAN module, SEEED Grove E5.
e5_uart = busio.UART(
    board.TX, board.RX, 
    baudrate=9600, 
    timeout=0.01,                 # need some timeout for readline() to work.
    receiver_buffer_size=128,     # when downlink is received, about 90 bytes are received.
)

# wait for join before sending reboot; join only occurs during power up.
time.sleep(8.0)
lora.send_reboot(e5_uart)
time.sleep(7.0)    # need to wait for send to continue.

# Send command to get ID info sent back from the E5
cmd = bytes('AT+ID\n', 'utf-8')
e5_uart.write(cmd)

# The object that reads the power and transmits readings.  Initially None but
# determined in the main loop
reader = None

while True:

    try:
        # Make sure correct reader is being used
        if config.detail:
            if type(reader) is not DetailReader:
                reader = DetailReader(e5_uart)
                print('made detail')
        else:
            if type(reader) is not AverageReader:
                reader = AverageReader(e5_uart)
                print('made average')

        # Read sensor and potentially send data
        reader.read()

        # Read any lines that have been sent by the E5 module.  Check to 
        # see if they are downlinks & process if so.
        while True:
            lin = e5_uart.readline()
            if lin is None: break
            try:
                lin_str = str(lin, 'ascii').strip()
                print(lin_str)
                lora.check_for_downlink(lin_str, e5_uart)
            except:
                print('Bad character in line:', lin)

    except KeyboardInterrupt:
        sys.exit()
    
    #except:
    #    print('Unknown error.')
