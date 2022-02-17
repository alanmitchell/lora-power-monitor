"""CircuitPython code to measure electrical power and transmit data via LoRaWAN.
The radio module used is a SEEED Studio Grove E5. Voltage is sampled from an 
Jameco 5VAC power adapter and current sampled from a CR Magnetics CR 3110-3000 CT.
Both current and voltage waveforms are connected to a 2.048 Volt reference voltage 
so that the AC voltage swing stays within limits of the microcontroller ADC.
"""
import time
import board
import busio

from detail_power_reader import DetailReader
from average_power_reader import AverageReader

# Serial port talking to LoRaWAN module, SEEED Grove E5.
e5_uart = busio.UART(
    board.TX, board.RX, 
    baudrate=9600, 
    timeout=0.01,                 # need some timeout for readline() to work.
    receiver_buffer_size=128,     # when downlink is received, about 90 bytes are received.
)

def send_reboot():
    """Send a message indicating that a reboot occurred."""
    print('reboot')     # debug print
    cmd = bytes('AT+MSGHEX="02"\n', 'utf-8')
    e5_uart.write(cmd)

def check_for_downlink(lin):
    """'lin' is a line received from the E5 module.  Check to see if it is
    a Downlink message, and if so, process the request."""
    lin = str(lin)
    if 'PORT: 1; RX: "' in lin:
        # this is a Downlink message. Pull out the Hex string data.  First two
        # characters indicate the request type.
        data = lin.split('"')[-2]
        if data[:2] == '01':
            # Request to change Data Rate. Data rate is given in the 3rd & 4th 
            # charagers.
            dr = int(data[2:4])
            cmd = bytes('AT+DR=%s\n' % dr, 'utf-8')
            e5_uart.write(cmd)

send_reboot()
time.sleep(7.0)    # need to wait for send to continue.

# reader that sends signifcant changes in power consumption
#reader = DetailReader(e5_uart)    
reader = AverageReader(e5_uart)

while True:

    # Read sensor and potentially send data
    reader.read()

    # Read any lines that have been sent by the E5 module.  Check to 
    # see if they are downlinks & process if so.
    while True:
        lin = e5_uart.readline()
        if lin is None: break
        print(lin)
        check_for_downlink(lin)
