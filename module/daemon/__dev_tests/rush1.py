import sys, os
from datetime import datetime
import time
from module import log

loop = 3

try:
    if len(sys.argv) >= 2:
        infile = sys.argv[1]
        fn = datetime.now().strftime("%Y%m%d%H%M%S%f") + "_" + os.path.basename(infile) + ".out"
        with open(infile, 'r') as fi:
            ll = fi.read()
            with open(fn, 'w') as fo:
                for i in range(loop):
                    fo.write("%d : %s\n" % (i, ll))
                    time.sleep(1)
except:
    log.exception()
