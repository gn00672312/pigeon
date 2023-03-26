# -*- coding: utf-8 -*-
from __future__ import (
    absolute_import,
    print_function
)

import os
import sys
import shutil

import unittest
import time
from multiprocessing import Process
import threading
from module import log

os.environ['COLLECTIVE_NAME'] = 'super_test'

from tests import (
    AbsTestFileDrive
)

CWD_PATH = os.path.dirname(os.path.abspath(__file__))
OUTSIDE_LOOP_NUM = 12
LOOP_NUM = 60
WAIT_TIMES = 10


class TestSuperPressure(AbsTestIFileDrive):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test(self):
        filedrived = self._create_filedrive(['RUSH'])
        ffs = [ 'r-%d' % i for i in range(2)]
        thread_event = threading.Event()
        p = Process(target=filedrived.startup,
            args=[ (OUTSIDE_LOOP_NUM) * (LOOP_NUM + 1) * 60 * WAIT_TIMES, ])
        p.start()

        for idx in range(OUTSIDE_LOOP_NUM):
            for i in range(LOOP_NUM):
                self.create_a_lot_files()
                time.sleep(60)
            time.sleep(20 * LOOP_NUM)

        for ww in range(LOOP_NUM * WAIT_TIMES):
            if len(os.listdir(self.tst_root)) == 0:
                break
            log.event(">>>>>>> wait times : ", ww)
            time.sleep(60)

        p.terminate()

        fcount = 0
        for ff in os.listdir(CWD_PATH):
            if ff.endswith(".out"):
                fcount += 1
                os.remove(ff)
        log.event(">>>>>>> total output file numbers: ", fcount)

        monifiles = len(os.listdir(self.tst_root))
        self.assertEqual(monifiles, 0)

        # clear files
        shutil.rmtree(self.tst_root)
        fadir = os.path.join(CWD_PATH, "__dev_tests", "archive", "failure")
        for ff in os.listdir(fadir):
            os.remove(os.path.join(fadir, ff))



    def create_a_lot_files(self):
        time.sleep(1)
        ffs = [ 'r-%d' % i for i in range(2, 20)]
        self._create_files(ffs, 0.01)

        time.sleep(1)
        ffs = [ 'r-%d' % i for i in range(20, 30)]
        self._create_files(ffs, 0.01)

        time.sleep(1)
        ffs = [ 'r-%d' % i for i in range(30, 100)]
        self._create_files(ffs, 0.01)

        self._create_files(['fail1', 'crash1'], 0.01)

        time.sleep(10)
        ffs = [ 'r-%d' % i for i in range(0, 20)]
        self._create_files(ffs, 0.01)

        self._create_files(['fail2', 'crash2'], 0.01)


if __name__ == "__main__":
    unittest.main()
