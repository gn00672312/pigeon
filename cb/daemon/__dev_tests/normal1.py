import sys, os
import time
from module import log

fname = 'normal1_output.out'
if len(sys.argv) >= 2:
    fname = sys.argv[1] + ".1.out"
try:
    file_output = open(fname, 'w')
    file_output.close()
    log.diag(file_output)
except:
    log.exception()


loop = 5
if len(sys.argv) >= 3:
    try:
        loop = int(sys.argv[2])
    except:
        pass

for i in range(loop):
    log.diag(">>>>> processing... %d" % (i))
    time.sleep(1)

log.diag('file exists: ', os.path.exists(fname))
log.diag("cwd: ", os.getcwd())
