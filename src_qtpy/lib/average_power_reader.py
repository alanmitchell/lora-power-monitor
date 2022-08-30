"""Reads and averages power over a fixed time interval.
"""
from config import config
from base_reader import BaseReader
import power_measure

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

        avg_power = self.reading_total / config.reads_between_xmit
        print(avg_power)

        # transmit the average expressed as tenths of a Watt, as a 2-byte HEX integer
        msg += '%04X' % int(avg_power * 10.0 + 0.5)

        # add the timestamp offset, which should be half the measurement interval
        # expressed in seconds
        offset = config.secs_between_xmit / 2.0
        msg += '%04X' % int(offset)

        self.send_data(msg)     # use parent class function to send

    def read(self):

        self.ix += 1
        self.reading_total += power_measure.measure()

        if self.ix >= config.reads_between_xmit:
            self.send_pwr_readings()
            self.ix = 0
            self.reading_total = 0.0
