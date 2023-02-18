# Functions releated to LoRa communication

from config import config

def send_reboot(e5_uart):
    """Send a message indicating that a reboot occurred."""
    print('reboot')     # debug print
    cmd = bytes('AT+MSGHEX="02"\n', 'utf-8')
    e5_uart.write(cmd)

def check_for_downlink(lin, e5_uart):
    """'lin' is a line received from the E5 module.  Check to see if it is
    a Downlink message, and if so, process the request."""
    if 'PORT: 1; RX: "' in lin:
        # this is a Downlink message. Pull out the Hex string data.  First two
        # characters indicate the request type.
        data = lin.split('"')[-2]
        if data[:2] == '01':
            # Request to change Data Rate. Data rate is given in the 3rd & 4th 
            # characters.
            dr = int(data[2:4], 16)
            if dr in (0, 1, 2, 3):
                cmd = bytes('AT+DR=%s\n' % dr, 'utf-8')
                e5_uart.write(cmd)

        elif data[:2] == '02':
            # Request to change Detail mode: 1 is Detail mode, 0 is Average mode
            mode = int(data[2:4], 16)
            config.detail = mode

        elif data[:2] == '03':
            # Request to change time between transmissions, 2 byte (4 Hex characters)
            secs = int(data[2:6], 16)
            print('Setting time between transmits to', secs, 'seconds')
            config.secs_between_xmit = secs
