import sys, os
import time
from module import log


def write_something(file_path, text):
    with open(file_path, 'a') as fout:
        fout.write(text)


fname = 'time_output.out'
if len(sys.argv) >= 2:
    fname = sys.argv[1] + ".out"
try:
    write_something(fname, '1')
except:
    log.exception()


