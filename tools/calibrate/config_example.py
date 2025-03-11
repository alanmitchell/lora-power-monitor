# Total number of readings to take for calibration
TOTAL_READS = 20

# Calibration multiplier to correct the reading from the actual power measurement
# device, most likely a PZEM-004T.
ACTUAL_CALIB_MULT = 1.01

# Number of turns captured by the CT of the LoRaWAN power monitor.
TURNS = 7

# Path to the calibrate.py file on the LoRa Power Monitor
# Comment out one of the following, using a # character

# Path for Linux Computer:
CALIBRATE_PATH = "/media/alan/CIRCUITPY/calibrate.py"

# Path for Windows:
#CALIBRATE_PATH = "D:\calibrate.py"
