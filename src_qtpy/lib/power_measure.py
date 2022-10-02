"""Module that performs the power measurement by reading the voltage and current
signals and computing power.
"""
import board
from analogio import AnalogIn
#from digitalio import DigitalInOut, Direction
import gc

from config import config

# get the configuration object from the directory above
import sys
sys.path.insert(0, '../')
import calibrate

# Weighting to put on current voltage reading relative to prior for
# calculating power.  Adjusts for phase shifts between current and voltage
# sensing.
CUR_V_WT = 0.97

# Samples to take. Will run out of memory if too many. It takes 106 - 109
# to cover one 60 Hz cycle.
SAMPLES = 110 * 8

# Identify the pins that have the voltage, current and reference voltage.
v_in = AnalogIn(board.A0)
i_in = AnalogIn(board.A1)
vref_in = AnalogIn(board.A2)

#debug_out = DigitalInOut(board.SDA)
#debug_out.direction = Direction.OUTPUT
#debug_out.value = False


def measure_once():
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

    # collect all the samples.  106 - 109 samples covers a full cycle
    n = SAMPLES
    v_arr = [0] * n
    i_arr = [0] * n

    #debug_out.value = True
    for i in range(n):
        v_arr[i] = v_in.value          # I'm reading v_in first, so already accounting for some of the lead
        i_arr[i] = i_in.value
    #debug_out.value = False

    # find first and last positive-slope zero-crossing so we calculate power across a set of 
    # complete cycles.
    ix_start = 1          # default if no zero crossing is found
    for i in range(1, n):
        if v_arr[i] >= vref and v_arr[i-1] < vref:
            ix_start = i
            break
    
    ix_end = n - 1
    for i in range(1, n):
        if v_arr[-i] >= vref and v_arr[-i-1] < vref:
            ix_end = n - i - 1
            break

    # calculate power
    pwr = 0.0
    for i in range(ix_start, ix_end + 1):
        v_wtd = v_arr[i] * CUR_V_WT + v_arr[i-1] * (1.0 - CUR_V_WT)
        pwr += (v_wtd - vref) / vref * (i_arr[i] - vref) / vref
    pwr = pwr * calibrate.CALIB_MULT / (ix_end - ix_start + 1)

    return pwr

def measure():
    pwr = 0.0
    ct = 3
    for i in range(ct):
        gc.collect()
        pwr += measure_once()
        #print(gc.mem_free())
        gc.collect()
    pwr /= ct

    if pwr < -1.0:
        # CT is reversed
        pwr = -pwr
    elif pwr < 0.0:
        # noise made it less than 0
        pwr = 0.0

    print('val', pwr, calibrate.CALIB_MULT)

    return pwr
