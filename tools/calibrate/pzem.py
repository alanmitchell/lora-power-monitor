"""Reads the power from a PZEM power measurement device that supports MODBUS.
"""
import minimalmodbus

minimalmodbus.CLOSE_PORT_AFTER_EACH_CALL=True

def read_power(port_path, calibration_mult):
    instr = minimalmodbus.Instrument(port_path, 1)
    instr.serial.timeout = 0.1
    instr.serial.baudrate = 9600
    data = None
    for i in range(5):
        try:
            data = instr.read_registers(0, 10, 4)
            break
        except IOError as e:
            print('Error')
            pass
    if data:
        return (data[3] + data[4] * 65536) * 0.1 * calibration_mult
    else:
        return None
