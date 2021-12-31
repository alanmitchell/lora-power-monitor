"""CircuitPython code to measure electrical power and transmit data via LoRaWAN.
The radio module used is a SEEED Studio Grove E5. Voltage is sampled from an 
Jameco 5VAC power adapter and current sampled from a CR Magnetics CR 3110-3000 CT.
Both current and voltage waveforms are connected to a 2.048 Volt reference voltage 
so that the AC voltage swing stays within limits of the microcontroller ADC.
"""
import time
import board
import busio
from analogio import AnalogIn
#from digitalio import DigitalInOut, Direction

# Constants that control when power readings are sent via LoRaWAN:
PCT_CHG_THRESH = 0.03     # Power must change by at least this percent, expressed as 
                          #    fraction, i.e. 0.03 is 3%
ABS_CHG_THRESH = 2.0      # Power must change by at least this many Watts
MAX_READING_GAP = 600     # If haven't sent in this number of measurements, force a send
MIN_READING_GAP = 7       # LoRaWAN radio can't accept readings too close in time. Min gap
                          #    expressed in number of measurements.

CYCLES_TO_MEASURE = 60       # full cycles to measure for one reading

# Calibration point was 870 Watts.  PZEM meter - 0.35% was source of truth.
CALIB_MULT = 27368.0          # multiplier to convert v * i measured into Watts

# Identify the pins that have the voltage, current and reference voltage.
v_in = AnalogIn(board.A0)
i_in = AnalogIn(board.A1)
vref_in = AnalogIn(board.A2)
#debug_out = DigitalInOut(board.A3)
#debug_out.direction = Direction.OUTPUT

# Serial port talking to LoRaWAN module, SEEED Grove E5.
uart = busio.UART(
    board.TX, board.RX, 
    baudrate=9600, 
    timeout=0.01,                 # need some timeout for readline() to work.
    receiver_buffer_size=128,     # when downlink is received, about 90 bytes are received.
)

def measure_power():
    """Returns average power measured across CYCLES_TO_MEASURE full AC
    cycles.
    In order to not exceed resolution of single-precision float variable,
    calculate average power for each cycle, and then average the cycle values.
    """

    # Start by getting a good average for the reference voltage
    n_ref = 50
    vref = 0
    for i in range(n_ref):
        vref += vref_in.value
    vref /= n_ref

    v1 = 0.0           # prior voltage reading
    v2 = 0.0           # two prior voltage reading
    pwr_avg = 0.0
    cycle_tot = 0.0
    n = 0
    cycle_starts = 0

    invert = False      # negate reading if True.
    while True:
        i = i_in.value
        v = v_in.value
        v = (v - vref) / vref
        i = (i - vref) / vref

        if v1 < 0.0 and v2 < 0.0 and v >= 0.0:
            # a new cycle has started with this reading
            cycle_starts += 1

            if cycle_starts > 1:
                # calculate average power from last cycle and add to running total
                # for all cycles.  reset cycle counters.
                cycle_tot /= n
                pwr_avg += cycle_tot
                # if large enough power, determine whether inverted
                if abs(cycle_tot * CALIB_MULT) > 6.0:
                    invert = (cycle_tot < 0)
                cycle_tot = 0.0
                n = 0

            if cycle_starts > CYCLES_TO_MEASURE:
                pwr_avg /= CYCLES_TO_MEASURE
                pwr_avg *= CALIB_MULT
                if invert:
                    pwr_avg = -pwr_avg
                # don't return negative values
                if pwr_avg < 0.0:
                    pwr_avg = 0

                return pwr_avg
        
        if cycle_starts > 0:
            # because of delay in reading voltage relative to current, interpolate the 
            # voltage back to the time the current was read by weighting in prior reading.
            # v1 weighting is determined by length of time for one analog read / total time
            # for one sample including all the code.
            cycle_tot += (v * 0.79 + v1 * 0.21) * i
            n += 1
        
        v2 = v1
        v1 = v

def send_pwr_readings(pwr_list):
    """Sends power readings in 'pwr_list' list to the LoRaWAN module.
    """
    print(pwr_list)     # debug print
    msg = 'AT+MSGHEX="01'

    # assemble readings into 2-byte values, units are 0.1 W
    for pwr in pwr_list:
        msg += '%04X' % int(pwr * 10.0 + 0.5)
    msg += '"\n'
    cmd = bytes(msg, 'utf-8')
    uart.write(cmd)

def send_reboot():
    """Send a message indicating that a reboot occurred."""
    print('reboot')     # debug print
    cmd = bytes('AT+MSGHEX="02"\n', 'utf-8')
    uart.write(cmd)

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
            uart.write(cmd)

send_reboot()
time.sleep(7.0)    # need to wait for send to continue.

# The last power value that was sent (Watts)
pwr_last_sent_value = None

# counter that track how many measurements since last power value was sent
ix = MAX_READING_GAP      # ensures that a reading will be sent immediately

# track the one-prior power reading because that is sent along with the new value
pwr_prior = None

while True:
    ix += 1
    pwr = measure_power()
    #print(pwr)
    do_send = False
    # Need to have one prior reading at least before sending.
    if pwr_prior is not None:
         
        if pwr_last_sent_value is not None:
            # Check absolute change and percent change to see if enough change has occurred
            # to send a reading.
            do_send = abs(pwr - pwr_last_sent_value) >= ABS_CHG_THRESH
            if pwr_last_sent_value != 0.0:
                do_send = do_send and abs((pwr - pwr_last_sent_value) / pwr_last_sent_value) >= PCT_CHG_THRESH
        else:
            # Nothing has been sent yet, so send a reading.
            do_send = True

        # If we exceeded max measure count, send no matter what.
        if ix >= MAX_READING_GAP: do_send = True

        # if we haven't waited long enough since last send, don't send.
        if ix < MIN_READING_GAP: do_send = False

        if do_send:
            send_pwr_readings([pwr_prior, pwr])
            pwr_last_sent_value = pwr
            ix = 0

    pwr_prior = pwr
    #print(ix)    # debug print

    # Read any lines that have been sent by the E5 module.  Check to 
    # see if they are downlinks & process if so.
    while True:
        lin = uart.readline()
        if lin is None: break
        print(lin)
        check_for_downlink(lin)
