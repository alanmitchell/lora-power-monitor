"""Contains base class for implementing sensor readers that are polled
each time through the main script loop.  Also contains infrastructure
for sending reading values to the LoRa-E5 module via a UART.
"""

class BaseReader:
    """Reader classes should inherit from this class, which provides access to the
    LoRa-E5 module for sending LoRaWAN data.
    """

    def __init__(self, e5_uart, secs_per_loop):

        # store reference to the UART object that communicates with the
        # SEEED LoRa-E5 module.
        self.uart = e5_uart

        # This is the number of seconds it takes to execute the main loop once.
        # Used to calculate certain loop counts in child classes.
        self.secs_per_loop = secs_per_loop

    def send_data(self, msg):
        """Sends the HEX string 'msg' to the E5 module with a AT+MSGHEX command.
        """
        final_msg = 'AT+MSGHEX="' + msg + '"\n'

        cmd = bytes(final_msg, 'utf-8')
        self.uart.write(cmd)

    def read(self):
        raise NotImplementedError('The read method needs to be implmented.')