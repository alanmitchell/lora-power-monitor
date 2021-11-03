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
CALIB_MULT = 6599.0          # multiplier to convert v * i measured into Watts

# Identify the pins that have the voltage, current and reference voltage.
v_in = AnalogIn(board.A0)
i_in = AnalogIn(board.A1)
vref_in = AnalogIn(board.A2)

# Serial port dumping debug information now but ultimately for talking the 
# LoRaWAN transceiver module.
uart = busio.UART(board.TX, board.RX, baudrate=9600)

def measure_power():
    """Returns average power measured across CYCLES_TO_MEASURE full AC
    cycles.
    In order to not exceed resolution of single-precision float variable,
    calculate average power for each cycle, and then average the cycle values.
    """

    v1 = 0.0
    v2 = 0.0
    pwr_avg = 0.0
    cycle_tot = 0.0
    n = 0
    cycle_starts = 0

    invert = False      # negate reading
    while True:
        vref = vref_in.value
        v = v_in.value
        i = i_in.value
        v = (v - vref) / vref
        i = (i - vref) / vref

        if v1 < 0.0 and v2 < 0.0 and v >= 0.0:
            # a new cycle has started with this reading
            cycle_starts += 1

            if cycle_starts == 1:
                # the first cycle has started
                st = time.monotonic()
            else:
                # calculate average power from last cycle and add to running total
                # for all cycles.  reset cycle counters.
                cycle_tot /= n
                pwr_avg += cycle_tot
                # if large enough power, determine whether inverted
                if abs(cycle_tot * CALIB_MULT) > 1.5:
                    invert = (cycle_tot < 0)
                cycle_tot = 0.0
                n = 0

            if cycle_starts > CYCLES_TO_MEASURE:
                t_exec = time.monotonic() - st
                pwr_avg /= CYCLES_TO_MEASURE
                pwr_avg *= CALIB_MULT
                if invert:
                    pwr_avg = -pwr_avg
                return pwr_avg, t_exec
        
        if cycle_starts > 0:
            cycle_tot += v * i
            n += 1
        
        v2 = v1
        v1 = v


while True:
    pwr, t_exec = measure_power()
    print(t_exec, pwr)
    out = bytes('%s\n' % pwr, 'utf-8')
    uart.write(out)
    #time.sleep(0.5)