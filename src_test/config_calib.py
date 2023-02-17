# Serial port of multimeter
PORT_VOLT = '/dev/ttyUSB0'

# Serial port of LoRa Power Meter
PORT_PWR = '/dev/ttyACM0'

# Total number of readings to take for calibration
TOTAL_READS = 20

# Calibration multiplier to convert read voltage into actual voltage
VOLT_CALIB_MULT = 1.00       

# Limits on voltage, reject if outside these
V_MIN = 110.0
V_MAX = 130.0

# Number of turns captured by the CT
TURNS = 20

# Load resistances
LOAD_R = 751.0       # 25W Power resistor
#LOAD_R = 9617.       # 2 H Inductor
#LOAD_R = 22069.      # 3 x 1 uF Ceramic Caps

