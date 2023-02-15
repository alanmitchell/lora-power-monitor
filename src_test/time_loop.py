#!/usr/bin/env python

# Determine average time to do a power measurement.  Needed for the 
# SECS_PER_LOOP setting in the config.py file in the main application.
from serial import Serial
from time import time

p = Serial('/dev/ttyACM0', 115200)

st = None
ix = 0
iterations = 30
for i in range(iterations):
    lin = p.readline().decode('utf-8').strip()
    if 'val' not in lin:
        continue
    if st is None:
        st = time()
    else:
        ix += 1
    print(lin)
elapsed = time() - st
print('%.4f' % (elapsed / ix))
