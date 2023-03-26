import os, sys
import unittest

HOME = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if HOME not in sys.path:
    sys.path.append(HOME)

import module.log as log


class ModuleLogTest(unittest.TestCase):

    def x_test_pure(self):
        log.diag("test_pure")

    def x_test_env(self):
        os.environ["LOG_NAME"] = "log_test"
        os.environ["COLLECTIVE_NAME"] = "collect_test"
        log.diag("test_env")

    def test_log_conf(self):
        os.environ["LOG_CONFIG"] = "log.conf"
        # log.set_log_config("log_test.conf")
        log.set_collective_name("collect_test")
        log.verbose("test_log_conf 1")


if __name__ == '__main__':
    unittest.main()
