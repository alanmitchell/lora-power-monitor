"""CircuitPython code to measure electrical power.  Voltage is sampled from an 
AC/AC power adapter and current sampled from a CT.  Both current and voltage
waveforms are connected to a reference voltage part way between microcontroller
Vcc and ground.
"""
import time
import board
import busio
from analogio import AnalogIn

CYCLES_TO_MEASURE = 60       # full cycles to measure for one reading
CALIB_MULT = 21308.0          # multiplier to convert v * i measured into Watts

# Identify the pins that have the voltage, current and reference voltage.
v_in = AnalogIn(board.A0)
i_in = AnalogIn(board.A1)
vref_in = AnalogIn(board.A2)

# Serial port dumping debug information now but ultimately for talking the 
# LoRaWAN transceiver module.
uart = busio.UART(board.TX, board.RX, baudrate=9600)

def prnu(x, newline=True):
    """Prints the string representation of the object x to the UART.
    """
    s = str(x) + ('\n' if newline else '')
    uart.write(bytes(s, 'utf-8'))

def measure_power():
    """Returns average power measured across CYCLES_TO_MEASURE full AC
    cycles.
    In order to not exceed resolution of single-precision float variable,
    calculate average power for each cycle, and then average the cycle values.
    """

    v1 = 0.0           # prior voltage reading
    v2 = 0.0           # two prior voltage reading
    pwr_avg = 0.0
    cycle_tot = 0.0
    n = 0
    cycle_starts = 0

    invert = False      # negate reading if True.
    while True:
        vref = vref_in.value
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
                return pwr_avg
        
        if cycle_starts > 0:
            # because of delay in reading voltage relative to current, interpolate the 
            # voltage back to the time the current was read by weighting in prior reading.
            cycle_tot += (v * 0.6667 + v1 * 0.3333) * i
            n += 1
        
        v2 = v1
        v1 = v


while True:
    pwr = measure_power()
    prnu(pwr)
    #prnu(vref_in.value)
    #time.sleep(1)