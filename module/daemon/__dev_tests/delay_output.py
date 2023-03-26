import sys, os
import time

fname = 'delay_output.out'
if len(sys.argv) >= 2:
    fname = sys.argv[1] + ".delay_output.out"

loop = 5
if len(sys.argv) >= 3:
    try:
        loop = int(sys.argv[2])
    except:
        pass

for i in range(loop):
    time.sleep(1)

file_output = open(fname, 'w')
file_output.close()
