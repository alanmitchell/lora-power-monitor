"""Holds configuration information and also stores/retrieves some settings
from non-volatile memory.
"""
from microcontroller import nvm        # non-volatile memory


# Starting indexes for values stored in non-volatile memory.
ADDR_DETAIL = 0    # Holds Detail boolean
ADDR_SECS_BETWEEN_XMIT = 1     # Index of 2-byte integer of # of seconds between transmission

class Configuration:

    # If no downlink has been made to change which reader is being used (Detailed
    # of Averaging), this is the default setting.
    # If DETAIL is set to True, this device will send power readings whenever a 
    # significant change occurs.  If set to False, average readings will be sent, 
    # with a period determined by the SECS_BETWEEN_XMIT constatn in the 
    # average_power_reader.py module.
    DETAIL_DEFAULT = False

    # Number of seconds per main loop (affected by speed of micro-controller)
    SECS_PER_LOOP = 1.0182

    # full AC cycles to measure for one power reading
    CYCLES_TO_MEASURE = 60       
    
    # --- Settings related to the Detail Power Reader
    # Constants that control when power readings are sent via LoRaWAN:
    PCT_CHG_THRESH = 0.03     # Power must change by at least this percent, expressed as 
                              #    fraction, i.e. 0.03 is 3%
    ABS_CHG_THRESH = 7.0      # Power must change by at least this many Watts

    # If haven't sent in this number of measurements, force a send.
    MAX_READING_GAP_SECS = 900
    MAX_READING_GAP = int(MAX_READING_GAP_SECS / SECS_PER_LOOP)

    # --- Settings related to Average Power Reader
    # If not changed by a downlink, this is the default number seconds between
    # transmission of an average power value.
    SECS_BETWEEN_XMIT_DEFAULT = 600

    def __init__(self):
        # for the few settings that are changeable via downlink, check non-volatile 
        # memory to see what value to use.  NVM bytes will be 255 if they have never
        # been written before.

        # Detail or Average mode
        nvm_val = nvm[ADDR_DETAIL]
        if nvm_val == 0:
            self._detail = False
        elif nvm_val == 1:
            self._detail = True
        else:
            self._detail = Configuration.DETAIL_DEFAULT

        # Seconds between Transmissions for Averaging mode
        nvm_val = nvm[ADDR_SECS_BETWEEN_XMIT] * 256 + nvm[ADDR_SECS_BETWEEN_XMIT + 1]
        if nvm_val != (2**16 - 1):
            self._secs_between_xmit = nvm_val
        else:
            self._secs_between_xmit = Configuration.SECS_BETWEEN_XMIT_DEFAULT

    @property
    def detail(self):
        """If True use Detailed reader, otherwise use Averaging Reader.
        """
        return self._detail

    @detail.setter
    def detail(self, val):
        if val in (0, 1):
            self._detail = val
            nvm[ADDR_DETAIL] = val

    @property
    def secs_between_xmit(self):
        """With the Averaging Reader, seconds between transmission
        of average values."""
        return self._secs_between_xmit

    @secs_between_xmit.setter
    def secs_between_xmit(self, val):
        if val < (2**16 - 1):
            self._secs_between_xmit = val
            nvm[ADDR_SECS_BETWEEN_XMIT] = (val >> 8)
            nvm[ADDR_SECS_BETWEEN_XMIT + 1] = (val & 0xFF)

    @property
    def reads_between_xmit(self):
        return int(self.secs_between_xmit / Configuration.SECS_PER_LOOP)

# Instantiate a Config object that will be imported by modules that need access
# to the configuration information.  So, those modules will execute:
#    from config import config
# to get this object.
config = Configuration()
