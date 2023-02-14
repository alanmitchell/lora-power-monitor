#!/usr/bin/env python

# Determine average time to do a power measurement.  Needed for the 
# config.py file in the main application.
from serial import Serial
from time import time

p = Serial('/dev/ttyACM0', 115200)

st = None
ix = 0
iterations = 30
for i in range(iterations):
    lin = p.readline()
    if st is None:
        st = time()
    else:
        ix += 1
    print(lin.decode('utf-8').strip())
elapsed = time() - st
print(elapsed / ix)