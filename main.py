"""CircuitPython code to measure electrical power.  Voltage is sampled from an 
AC/AC power adapter and current sampled from a CT.  Both current and voltage
waveforms are connected to a reference voltage part way between microcontroller
Vcc and ground.
"""
from adafruit_binascii import hexlify
import time
import board
import busio
from analogio import AnalogIn

# Constants that control when power readings are sent via LoRaWAN
PCT_CHG_THRESH = 0.03     # Power must change by at least this percent, expressed as 
                          #    fraction, i.e. 0.03 is 3%
ABS_CHG_THRESH = 2.0      # Power must change by at least this many Watts
MAX_READING_GAP = 300      # If haven't sent in this number of measurements, force a send
MIN_READING_GAP = 7       # LoRaWAN can't accept readings too close in time. Min gap
                          #    expressed in number of measurements.

CYCLES_TO_MEASURE = 60       # full cycles to measure for one reading
CALIB_MULT = 27368.0          # multiplier to convert v * i measured into Watts

# Identify the pins that have the voltage, current and reference voltage.
v_in = AnalogIn(board.A0)
i_in = AnalogIn(board.A1)
vref_in = AnalogIn(board.A2)

# Serial port dumping debug information now but ultimately for talking the 
# LoRaWAN transceiver module.
uart = busio.UART(
    board.TX, board.RX, 
    baudrate=9600, 
    timeout=0.01,
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
            cycle_tot += (v * 0.76 + v1 * 0.24) * i
            n += 1
        
        v2 = v1
        v1 = v

def send_pwr_readings(pwr_list):
    print(pwr_list)
    msg = b'\x01'

    # assemble readings into 2-byte values, units are 0.1 W
    for pwr in pwr_list:
        msg += int(pwr * 10.0 + 0.5).to_bytes(2, 'big')

    msghex = hexlify(msg)
    cmd = bytes('AT+MSGHEX="', 'utf-8') + msghex + bytes('"\n', 'utf-8')
    uart.write(cmd)

def send_reboot():
    print('reboot')
    msghex = hexlify(b'\x02')
    cmd = bytes('AT+MSGHEX="', 'utf-8') + msghex + bytes('"\n', 'utf-8')
    uart.write(cmd)

def check_for_downlink(lin):
    lin = str(lin)
    if 'PORT: 1; RX: "' in lin:
        data = lin.split('"')[-2]
        if data[:2] == '01':
            # Request to change Data Rate
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
    do_send = False
    if pwr_prior is not None:
         
        if pwr_last_sent_value is not None:
            do_send = abs(pwr - pwr_last_sent_value) >= ABS_CHG_THRESH
            if pwr_last_sent_value != 0.0:
                do_send = do_send and abs((pwr - pwr_last_sent_value) / pwr_last_sent_value) >= PCT_CHG_THRESH
        else:
            # if nothing has been sent yet, send a reading.
            do_send = True

        # If we exceeded max measure count, send
        if ix >= MAX_READING_GAP: do_send = True

        # if we haven't waited long enough since last send, don't send.
        if ix < MIN_READING_GAP: do_send = False

        if do_send:
            send_pwr_readings([pwr_prior, pwr])
            pwr_last_sent_value = pwr
            ix = 0

    pwr_prior = pwr
    print(ix)

    while True:
        lin = uart.readline()
        if lin is None: break
        print(lin)
        check_for_downlink(lin)
