# -*- coding: utf-8 -*-
import sys, os
import time
from module import log

loop = 15

for i in range(loop):
    log.diag(">>>>> processing... %d" % (i))
    time.sleep(1)

fname = 'timeout.out'
if len(sys.argv) >= 2:
    fname = sys.argv[1] + ".out"
try:
    file_output = open(fname, 'w')
    file_output.close()
    log.diag(file_output)
except:
    log.exception()

log.diag('file exists: ', os.path.exists(fname))
log.diag("cwd: ", os.getcwd())
