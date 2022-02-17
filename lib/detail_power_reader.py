"""This power reader class sends power readings when noticeable changes in
the power consumption occurs.  Power values are also sent every MAX_READING_GAP
times if no significant change has occurred.
"""
from base_reader import BaseReader
import power_measure

# Constants that control when power readings are sent via LoRaWAN:
PCT_CHG_THRESH = 0.03     # Power must change by at least this percent, expressed as 
                          #    fraction, i.e. 0.03 is 3%
ABS_CHG_THRESH = 2.0      # Power must change by at least this many Watts
# If haven't sent in this number of measurements, force a send.  The divisor is the number
# of seconds per main script loop.
MAX_READING_GAP = int(600/1.0167)     
MIN_READING_GAP = 7       # LoRaWAN radio can't accept readings too close in time. Min gap
                          #    expressed in number of measurements.

# States controlling the change detection and data sending process
ST_FIRST = 0       # First reading after reboot
ST_NORMAL = 1      # Normal, no change occurred, no max gap
ST_CHANGE = 2      # Significant power change occurred


class DetailReader(BaseReader):

    def __init__(self, *args, **kwargs):

        # pass all arguments on to parent class
        super().__init__(*args, **kwargs)

        # The last power value that was sent (Watts)
        self.pwr_last_sent_value = None

        # counter that tracks how many measurements since last power value was sent
        self.ix = MAX_READING_GAP      # ensures that a reading will be sent immediately

        self.state = ST_FIRST
        self.readings = []

    def send_pwr_readings(self):
        """Sends power readings in self.readings to the LoRaWAN module.
        """
        print(self.readings)     # debug print
        msg = '01'          # the type code for this message

        # assemble readings into 2-byte values, units are 0.1 W
        for pwr in self.readings:
            msg += '%04X' % int(pwr * 10.0 + 0.5)

        self.send_data(msg)     # use parent class function to send

    def is_change(self, current_read):
        """Returns True if change in readings meets significant criteria, False otherwise.
        """
        last_val = self.pwr_last_sent_value    # shortcut variable

        # If no value has been sent yet, a change has occurred.
        if last_val is None:
            return True
        
        # Check absolute change and percent change to see if enough change has occurred
        # to send a reading.
        result = abs(current_read - last_val) >= ABS_CHG_THRESH
        if last_val != 0.0:
            result = result and abs((current_read - last_val) / last_val) >= PCT_CHG_THRESH

        return result

    def read(self):
        """Called each pass through the main script loop.  Reads power and determmines
        whether to send data or not.  Then, sends the data if needed.
        """
        self.ix += 1

        pwr = power_measure.measure()
        self.readings.append(pwr)

        do_send = False
        if self.state == ST_NORMAL and self.ix >= MAX_READING_GAP:
            self.readings = self.readings[-1:]   # only send current reading
            do_send = True
        
        # Need to have one prior reading at least before sending.
        elif self.state == ST_FIRST:
            self.state  = ST_NORMAL

        elif self.state == ST_NORMAL:
            if self.ix < MIN_READING_GAP:
                # only keep current reading
                self.readings = self.readings[-1:]
            elif self.is_change(pwr):
                self.state = ST_CHANGE
            else:
                # only keep current reading
                self.readings = self.readings[-1:]
        
        elif self.state == ST_CHANGE:
            # once a total of 5 readings have been accumulated, send the data.
            if len(self.readings) == 5:
                do_send = True

        if do_send:
            self.send_pwr_readings()
            self.pwr_last_sent_value = pwr
            self.readings = []
            self.ix = 0
            self.state = ST_NORMAL
