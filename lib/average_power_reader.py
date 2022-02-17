"""Reads and averages power over a fixed time interval.
"""
from base_reader import BaseReader
import power_measure

# Number of read() calls before an average value should be sent.  The divisor
# in the formula below if the main script loop time
READS_BETWEEN_XMIT = int(900 / 1.0167)


class AverageReader(BaseReader):

    def __init__(self, *args, **kwargs):

        # pass all arguments on to parent class
        super().__init__(*args, **kwargs)

        # counter that tracks how many measurements since last power value was sent
        self.ix = 0

        # Accumulates power readings since last transmission
        self.reading_total = 0.0

    def send_pwr_readings(self):
        """Sends the average power reading to the LoRaWAN module, along with the number
        of seconds to subtract from the current time to timestamp the middle of the interval.
        """
        msg = '03'          # the type code for this message

        avg_power = self.reading_total / READS_BETWEEN_XMIT
        print(avg_power)

        # transmit the average expressed as tenths of a Watt, as a 2-byte HEX integer
        msg += '%04X' % int(avg_power * 10.0 + 0.5)

        # add the timestamp offset, which should be half the measurement interval
        # expressed in seconds
        offset = READS_BETWEEN_XMIT * 1.0167 / 2.0
        msg += '%04X' % int(offset)

        self.send_data(msg)     # use parent class function to 

    def read(self):

        self.ix += 1
        self.reading_total += power_measure.measure()

        if self.ix == READS_BETWEEN_XMIT:
            self.send_pwr_readings()
            self.ix = 0
            self.reading_total = 0.0
