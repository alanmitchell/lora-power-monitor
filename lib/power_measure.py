"""Module that performs the power measurement by reading the voltage and current
signals and computing power.
"""
import board
import busio
from analogio import AnalogIn

# get the configuration object from the directory above
import sys
sys.path.insert(0, '../')
from config import config

# Identify the pins that have the voltage, current and reference voltage.
v_in = AnalogIn(board.A0)
i_in = AnalogIn(board.A1)
vref_in = AnalogIn(board.A2)

def measure():
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
                if abs(cycle_tot * config.CALIB_MULT) > 6.0:
                    invert = (cycle_tot < 0)
                cycle_tot = 0.0
                n = 0

            if cycle_starts > config.CYCLES_TO_MEASURE:
                pwr_avg /= config.CYCLES_TO_MEASURE
                pwr_avg *= config.CALIB_MULT
                if invert:
                    pwr_avg = -pwr_avg
                # don't return negative values
                if pwr_avg < 0.0:
                    pwr_avg = 0

                if config.PRINT_POWER:
                    print(pwr_avg)

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
