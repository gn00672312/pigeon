# -*- coding: utf-8 -*-
from __future__ import (
    absolute_import,
    print_function
)

import os
import sys
import shutil
import threading
from multiprocessing import Process
import unittest
import time
from datetime import datetime

CWD_PATH = os.path.dirname(os.path.abspath(__file__))

os.environ['LOG_CONFIG'] = '__dev_tests/log.conf'


class bcolors:
    HEADER = '\x1b[35m'
    OKBLUE = '\x1b[34m'
    OKGREEN = '\x1b[32m'
    WARNING = '\x1b[33m'
    FAIL = '\x1b[31m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    def __init__(self):
        pass


try:
    from .filedrive import (
        FileDrive,
        DEFAULT_ARGS
    )
    from .timedrive import (
        TimeDrive
    )
    from .util import (
        ConfigError,
        scan,
        sort_by_mtime
    )
    from .cb_queue import (
        QueueManager
    )
except ValueError:
    print(bcolors.FAIL + "Cannot relative import in non-package" + bcolors.ENDC)
    print("try run")
    print(bcolors.OKGREEN + " $ export PYTHONPATH={0}:$PYTHONPATH".format(
        os.path.dirname(CWD_PATH)) + bcolors.ENDC)
    print(bcolors.OKGREEN + " $ python -m {0}.{1} ".format(
        os.path.basename(CWD_PATH),
        os.path.splitext(os.path.basename(__file__))[0]) + bcolors.ENDC)
    sys.exit(1)


from __dev_tests.tst_config_ctx_manager import (
    TstConfigCtxManager,
    read_conf,
    write_conf
)


"""
Test Target:
DIR_MONITOR
NUM_MAX_PROCESSOR
EXEC_TASK.delay
QUERE.?
"""


class TestReadFileDriveConf(unittest.TestCase):
    def setUp(self):
        self.config_filename = "tst_filedrive.conf"

    def tearDown(self):
        pass

    def create_config(self):
        pass

    def test_NORMAL(self):
        titles = ["NORMAL"]
        with TstConfigCtxManager(titles) as cf:
            conf = FileDrive.import_config(cf)
            self.assertIsInstance(conf, dict)
            self.assertEqual(conf['DIR_MONITOR'], os.path.join(CWD_PATH, '__dev_tests/tst_scan'))
            self.assertEqual(conf['NUM_MAX_PROCESSOR'], DEFAULT_ARGS['NUM_MAX_PROCESSOR']['val']) #no "NUM_MAX_PROCESSOR"
            self.assertEqual(conf['EXEC_TASK'][r'^(?P<file>1)$']['delay'], 5)
            self.assertEqual(conf['EXEC_TASK'][r'^(?P<file>3)$']['delay'], conf['SECS_DELAY_TO_PROCESS'])
            self.assertEqual(conf['EXEC_TASK'][r'^(?P<file>1)$']['action'][0]['timeout'], 20)
            self.assertEqual(conf['EXEC_TASK'][r'^(?P<file>1)$']['action'][1]['timeout'], 10)

            self.assertEqual(conf['QUEUE']['qa']['priority'], 1)
            self.assertEqual(conf['QUEUE']['default']['priority'], 99999999)

    def test_CONFIG_ERROR(self):
        titles = [
            "NUM_MAX_PROCESSOR_IS_0",
            "TASK_DELAY_IS_STRING",
            "TASK_DELAY_IS_NEGATIVE",
            "TASK_NO_SCRIPT_EXEC",
            "TIMEOUT_IS_STRING",
            "QUEUE_MAX_IS_0",
            "QUEUE_PRIORITY_IS_STRING",
            "SYNTAX_ERROR"
        ]

        for title in titles:
            print(">>>> ERROR TEST: %s\n" % title)
            with self.assertRaises(ConfigError) as error:
                with TstConfigCtxManager([title]) as cf:
                    conf = FileDrive.import_config(cf)

    def test_MULTI_SCRIPT(self):
        titles = ["MULTI_SCRIPT"]
        with TstConfigCtxManager(titles) as cf:
            conf = FileDrive.import_config(cf)
            self.assertEqual(conf['EXEC_TASK'][r'^(?P<file>1)$']['action'][1]['script'], "1.py")

    def test_EMPTY(self):
        titles = ["EMPTY"]

        with self.assertRaises(ConfigError) as error:
            with TstConfigCtxManager(titles) as cf:
                FileDrive.import_config(cf)

        # with TstConfigCtxManager(titles) as cf:
        #     conf = FileDrive.import_config(cf)
        #     self.assertEqual(conf['DIR_MONITOR'], DEFAULT_ARGS['DIR_MONITOR']['val'])
        #     self.assertEqual(conf['NUM_MAX_PROCESSOR'], DEFAULT_ARGS['NUM_MAX_PROCESSOR']['val'])
        #     self.assertEqual(conf['QUEUE'], DEFAULT_ARGS['QUEUE']['val'])

    def test_NO_SUCH_FILE(self):
        with self.assertRaises(ConfigError) as error:
            conf = FileDrive.import_config("this_is_no_such_file_test")


class TestScanDir(unittest.TestCase):
    def setUp(self):
        """
        create test dir and files
        """
        self.tst_root = os.path.join(CWD_PATH, "__dev_tests", "tst_scan")
        self.tst_files = [
            "a/b/1.txt"
            "3.txt",
            "1.txt",
            "a/1.txt",
        ]
        for f in self.tst_files:
            file_path = os.path.join(self.tst_root, f)
            if not os.path.exists(os.path.dirname(file_path)):
                os.makedirs(os.path.dirname(file_path))
            open(file_path, 'w').close()
            time.sleep(1)

    def tearDown(self):
        """
        remove test dir and files
        """
        shutil.rmtree(self.tst_root)

    def test_scan_dir_not_exist(self):
        self.assertEqual(scan("/opt/CC"), [])

    def test_scan(self):
        rs = scan(self.tst_root)
        self.assertEqual(len(rs), len(self.tst_files))
        for f in self.tst_files:
            file_path = os.path.join(self.tst_root, f)
            self.assertIn(file_path, rs)

    def test_sort(self):
        rs = scan(self.tst_root)
        rs = sort_by_mtime(rs)

        except_list = [os.path.join(self.tst_root, f) for f in self.tst_files]
        self.assertListEqual(rs, except_list)


class TestFileDriveGoThroughFiles(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        titles = ["NORMAL"]
        cls.config_filename = "tst_filedrive.conf"
        if os.path.exists(cls.config_filename):
            os.remove(cls.config_filename)

        write_conf(cls.config_filename, read_conf(titles))
        cls.filedrive = FileDrive(config_file=cls.config_filename)

        cls.tst_root = os.path.join(CWD_PATH, "__dev_tests", "tst_scan")
        cls.tst_files = [
            "1",
            "2",
            "3",
            "4",
        ]
        for f in cls.tst_files:
            file_path = os.path.join(cls.tst_root, f)
            if not os.path.exists(os.path.dirname(file_path)):
                os.makedirs(os.path.dirname(file_path))
            open(file_path, 'w').close()
            time.sleep(1)
        time.sleep(60)

    @classmethod
    def tearDownClass(cls):
        """
        remove test dir and files
        """
        if os.path.exists(cls.config_filename):
            os.remove(cls.config_filename)

        shutil.rmtree(cls.tst_root)

    def test_go_through_files(self):
        rs = scan(self.tst_root)
        rs = sort_by_mtime(rs)
        self.filedrive.go_through_files(rs)

        self.assertEqual(len(self.filedrive.qm.queue_ordered_dict['default']._queue), 1)
        self.assertEqual(self.filedrive.qm.queue_ordered_dict['qa']._queue[0][0],
                os.path.join(self.tst_root, "1"))


class AbsTestFileDrive(unittest.TestCase):
    def _create_filedrive(self, titles):
        self.config_filename = "tst_filedrive.conf"
        if os.path.exists(self.config_filename):
            os.remove(self.config_filename)
        write_conf(self.config_filename, read_conf(titles))
        return FileDrive(config_file=self.config_filename)

    def _create_files(self, tst_files, delay=1):
        self.tst_root = os.path.join(CWD_PATH, "__dev_tests", "tst_scan")
        for f in tst_files:
            file_path = os.path.join(self.tst_root, f)
            if not os.path.exists(os.path.dirname(file_path)):
                os.makedirs(os.path.dirname(file_path))
            with open(file_path, 'w') as fi:
                fi.write(datetime.now().strftime("%Y%m%d%H%M%S%f"))
            time.sleep(delay)

    def _check_and_delete_file(self, file_path):
        print(">>>>> Check file path: %s" % (file_path))
        self.assertTrue(os.path.exists(file_path))
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False

    def tearDown(self):
        """
        remove test dir and files
        """
        self.config_filename = "tst_filedrive.conf"
        if os.path.exists(self.config_filename):
            os.remove(self.config_filename)


class TestRunner(AbsTestFileDrive):
    def setUp(self):
        pass

    def test_FailCrash(self):
        filedrive = self._create_filedrive(["NORMAL"])
        self._create_files(
            ["3", "4",]
        )

        thread_event = threading.Event()
        thread = threading.Thread(target=filedrive.startup, args=[8, ])
        thread.start()

        time.sleep(6)
        self._check_and_delete_file(os.path.join(CWD_PATH, '__dev_tests/archive', "3"))
        self._check_and_delete_file(os.path.join(CWD_PATH, '__dev_tests/archive/failure', "4"))

        thread_event.set()

    def test_parallel_action(self):
        filedrive = self._create_filedrive(["NORMAL"])
        self._create_files(['1'])

        thread_event = threading.Event()
        thread = threading.Thread(target=filedrive.startup, args=[14, ])
        thread.start()

        # wait to launch process
        time.sleep(6)
        dev_tests_path = os.path.join(CWD_PATH, '__dev_tests', '1.out')
        self._check_and_delete_file(dev_tests_path)
        dev_tests_path = os.path.join(CWD_PATH, '1.1.out')
        self._check_and_delete_file(dev_tests_path)
        # wait process done
        time.sleep(5)
        data_path = os.path.join(CWD_PATH, '__dev_tests/archive/data', '1')
        archive_path = os.path.join(CWD_PATH, '__dev_tests/archive', '1')
        # cwd_path = os.path.join(CWD_PATH, '1')
        self._check_and_delete_file(data_path)
        self._check_and_delete_file(archive_path)
        # self._check_and_delete_file(cwd_path)

        thread_event.set()

    def test_series_action(self):
        filedrive = self._create_filedrive(["NORMAL"])
        self._create_files(['2'])

        thread_event = threading.Event()
        p = Process(target=filedrive.startup,
                    args=[24, ])
        p.start()

        time.sleep(6)
        self._check_and_delete_file(os.path.join(CWD_PATH, "2.out"))
        self.assertFalse(os.path.exists(os.path.join(CWD_PATH, "__dev_tests", "2.1.out")))
        # wait process done
        time.sleep(5)
        # wait aother process done
        time.sleep(6)
        self._check_and_delete_file(os.path.join(CWD_PATH, '__dev_tests', "2.1.out"))

        p.terminate()

    def test_flow(self):
        filedrive = self._create_filedrive(['INTEGRATE_TEST'])
        self._create_files(
            ['4a', '2', '3', '1', '5']
        )
        thread_event = threading.Event()
        thread = threading.Thread(target=filedrive.startup, args=[33, ])
        thread.start()

        time.sleep(2)
        self._create_files(
            ['6', '7', '8', '4b', '10']
        )

        time.sleep(10)
        self._check_and_delete_file(os.path.join(CWD_PATH, "4a.out"))
        self._check_and_delete_file(os.path.join(CWD_PATH, "2.out"))
        self._check_and_delete_file(os.path.join(CWD_PATH, "1.out"))

        time.sleep(5)
        self._check_and_delete_file(os.path.join(CWD_PATH, "3.out"))
        self._check_and_delete_file(os.path.join(CWD_PATH, "5.out"))
        self._check_and_delete_file(os.path.join(CWD_PATH, "6.out"))

        time.sleep(5)
        self._check_and_delete_file(os.path.join(CWD_PATH, "7.out"))
        self._check_and_delete_file(os.path.join(CWD_PATH, "8.out"))
        self._check_and_delete_file(os.path.join(CWD_PATH, "4b.out"))

        time.sleep(5)
        self._check_and_delete_file(os.path.join(CWD_PATH, "10.out"))

        thread_event.set()

    def test_lot_queue_num(self):
        filedrive = self._create_filedrive(['A_LOT_QUEUE_NUM'])
        ffs = [ 'a-%d' % i for i in range(10)]
        self._create_files(ffs, 0.01)
        ffs = [ 'b-%d' % i for i in range(10)]
        self._create_files(ffs, 0.01)

        thread_event = threading.Event()
        p = Process(target=filedrive.startup,
                    args=[30, ])
        p.start()

        time.sleep(30)

        p.terminate()

        fcount = 0
        for ff in os.listdir(CWD_PATH):
            if ff.endswith(".out"):
                fcount += 1
                os.remove(ff)
        self.assertEqual(fcount, 20)

        monifiles = len(os.listdir(self.tst_root))
        self.assertEqual(monifiles, 0)

        shutil.rmtree(self.tst_root)

    def test_timeout(self):
        filedrive = self._create_filedrive(['TIMEOUT'])
        self._create_files(
            ['test-default', 'test-timeout', 'test-pass']
        )

        thread_event = threading.Event()
        thread = threading.Thread(target=filedrive.startup, args=[33, ])
        thread.start()

        archive = os.path.join(CWD_PATH, "__dev_tests", "archive")
        time.sleep(10)
        self._check_and_delete_file(os.path.join(archive, "failure", "test-timeout"))
        time.sleep(5)
        self._check_and_delete_file(os.path.join(archive, "failure", "test-default"))
        time.sleep(10)
        self._check_and_delete_file(os.path.join(archive, "test-pass"))
        self._check_and_delete_file(os.path.join(archive, "test-pass.out"))

        thread_event.set()


class TestMove(AbsTestFileDrive):
    def setUp(self):
        pass

    def test_move(self):
        filedrive = self._create_filedrive(["NORMAL"])
        self._create_files(['m1', 'm2', 'm3'])
        filedrive.startup(3)
        time.sleep(1)
        self._check_and_delete_file(os.path.join(self.tst_root, "m1"))

        self._check_and_delete_file(os.path.join(CWD_PATH, "__dev_tests", "a1", "m2"))
        self._check_and_delete_file(os.path.join(CWD_PATH, "__dev_tests", "a2", "m2-2"))
        self._check_and_delete_file(os.path.join(CWD_PATH, "__dev_tests", "m3"))


class AbsTestTimeDrive(unittest.TestCase):
    config_filename = "tst_timedrive.conf"

    def _create_timedrive(self, titles):
        if os.path.exists(self.config_filename):
            os.remove(self.config_filename)
        write_conf(self.config_filename, read_conf(titles, 'timedrive.conf'))
        return TimeDrive(config_file=self.config_filename)

    def _check_and_delete_file(self, file_path):
        print(">>>>> Check file path: %s" % (file_path))
        self.assertTrue(os.path.exists(file_path))
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False

    def _check_times(self, count, file_path):
        self.assertTrue(os.path.exists(file_path))
        if os.path.exists(file_path):
            with open(file_path, 'r') as fin:
                txt = fin.read()
            os.remove(file_path)
            self.assertEqual(count, len(txt))

    def tearDown(self):
        """
        remove test dir and files
        """
        if os.path.exists(self.config_filename):
            os.remove(self.config_filename)


class TestTimeDrive(AbsTestTimeDrive):
    def setUp(self):
        pass

    def tests_normal(self):
        timedrive = self._create_timedrive(['NORMAL'])
        timedrive.scheduler_startup()

        timedrive.check_jobs()
        time.sleep(9)
        timedrive.shutdown()
        self._check_times(2, '123.out')

    def tests_timeout(self):
        timedrive = self._create_timedrive(['TIME_OUT'])
        timedrive.scheduler_startup()

        loop = 20
        for i in range(loop):
            time.sleep(0.4)
            timedrive.check_jobs()
        timedrive.shutdown()
        self._check_times(4, '123.out')


if __name__ == "__main__":
    unittest.main()
