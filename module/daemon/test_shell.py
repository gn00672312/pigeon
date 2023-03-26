# -*- coding: utf-8 -*-
from __future__ import (
    absolute_import,
    print_function
)

import os
import sys
import unittest
import time

os.environ['COLLECTIVE_NAME'] = 'test'

from shell import Shell

CWD_PATH = os.path.dirname(os.path.abspath(__file__))

# PYTHON = '/usr/local/bin/python3.6'
PYTHON = '/usr/bin/python'


class TestShell(unittest.TestCase):

    def _check_and_delete_file(self, file_path):
        self.assertTrue(os.path.exists(file_path))
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False

    def test_normal(self):
        args = [PYTHON, '__dev_tests/delay_output.py']
        kwargs = {}
        sh = Shell(timeout=None)
        sh.run(*args, **kwargs)
        sh.wait()
        self._check_and_delete_file(os.path.join(CWD_PATH, "delay_output.out"))

    def xtest_wait_timeout(self):
        #
        # Not support TimeoutExpired under python 3.3 and will fail in this case
        #
        args = [PYTHON, '__dev_tests/delay_output.py']
        kwargs = {}
        sh = Shell(timeout=2)
        sh.run(*args, **kwargs)
        sh.wait()
        self.assertFalse(os.path.exists(os.path.join(CWD_PATH, "delay_output.out")))

    def test_check_timeout(self):
        args = [PYTHON, '__dev_tests/delay_output.py']
        kwargs = {}
        sh = Shell(timeout=2)
        sh.run(*args, **kwargs)
        for i in range(10):
            time.sleep(1)
            if sh.done():
                break

        self.assertFalse(os.path.exists(os.path.join(CWD_PATH, "delay_output.out")))


if __name__ == "__main__":
    unittest.main()
