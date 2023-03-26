# -*- coding: utf-8 -*-
from __future__ import (absolute_import, print_function)
import os
import signal
import time
import errno
import shutil
import datetime
import platform

from .util import ConfigError

try:
    from module import log
except ImportError:
    import logging as log
    log_filename = datetime.datetime.now().strftime("%Y%m%d_%H%M%S.log")
    log.basicConfig(
        level=log.DEBUG,
        format='%(asctime)s %(filename)s %(lineno)d %(levelname)-8s %(message)s',
        datefmt='%m-%d %H:%M:%S',
        # filename=log_filename
    )
    log.event = log.info

WINDOWS_PLATFORM = platform.system() == "Windows"

if not WINDOWS_PLATFORM:
    import fcntl


class Process(object):
    """
    Process can be the top level base class of any Linux daemon-like process.
    """
    '''
    FORMAT = 'format'
    YMDHMS = '%Y%m%d%H%M%S'
    TIMESTAMP_UTC = re.compile(r'\{timestamp_utc(\|(?P<format>[^ }]+))*}')
    TIMESTAMP_LST = re.compile(r'\{timestamp_lst(\|(?P<format>[^ }]+))*}')
    '''

    def __init__(self, config_file=None):
        self.TERMINATING = False
        self.__lock_file = None
        self.__pid_file = None

        process_dir = os.path.dirname(__file__)
        self.default_config_dir = os.path.join(process_dir, "conf")
        # self.default_config_name = os.path.basename(__file__).split(".")[0]
        self.default_config_name = '%s.conf' % self.__class__.__name__.lower()
        self.default_config_path = [
            os.path.join(process_dir, self.default_config_name),
            os.path.join(self.default_config_dir, self.default_config_name)
        ]
        self.config_file = config_file
        self.need_reload_config = True

    def set_pid_file(self, pid_file):
        self.__pid_file = pid_file
        if not os.path.isabs(pid_file):
            self.__pid_file = os.path.abspath(pid_file)

    @staticmethod
    def mtime_age(path):
        try:
            return time.time() - os.path.getmtime(path)
        except:
            # No age no matter why we can't get mtime.
            return 0

    @staticmethod
    def move(path_from, path_to):
        try:
            if path_to != os.path.devnull:
                os.makedirs(os.path.dirname(path_to))
                # Hard link first. It's lighter than real move (copy/delete).
                try:
                    os.link(path_from, path_to)
                    os.remove(path_from)
                except:
                    shutil.move(path_from, path_to)
            log.event('File moved: ', path_from, ' --> ', path_to)
            return True
        except:
            log.exception('Error moving file: ', path_from, ' --> ', path_to)
            return False

    @staticmethod
    def daemonize():
        """
        Let a process to be a daemon, a.k.a. service, process.
        """
        # Get the null device.
        if hasattr(os, "devnull"):
            dev_null = os.devnull
        else:
            dev_null = "/dev/null"

        # Try to the first fork.
        pid = os.fork()
        if pid != 0:
            # We are in parent. Just exits.
            os._exit(0)

        # To become the session leader of this new session and the
        # process group leader of the new process group.
        os.setsid()

        # Try to the second fork
        pid = os.fork()
        if pid != 0:
            # We are still in parent.
            os._exit(0)

        # From now, I am a daemon.
        # Change the working directory to root.
        os.chdir("/")

        # Clear any inherited file mode creation mask.
        os.umask(0)

        # Close file descriptors of stdin, stdout and stderr.
        for fd in range(0, 3):
            try:
                os.close(fd)
            except OSError:
                # We don't care this error.
                pass

        # These calls to open are guaranteed to return the lowest 3 file
        # descriptor, which will be 0 for stdin, 1 for stdout, 2 for stderr,
        # since they were closed above.
        os.open(dev_null, os.O_RDONLY)
        os.open(dev_null, os.O_WRONLY)
        os.open(dev_null, os.O_WRONLY)

    def install_signal_handlers(self):
        """
        Simply install a shutdown signal to handle normal ways of shutdown.
        If developers need more signal handlers, overwrite this method must
        be made by themselves.
        """
        def shutdown_handler(sig, frame):
            log.event('Shutdown signal received.')
            self.stop()

        signal.signal(signal.SIGINT, shutdown_handler)
        signal.signal(signal.SIGTERM, shutdown_handler)
        log.event('Shutdown signal handler installed.')

    @property
    def terminating(self):
        return self.TERMINATING

    @property
    def pid_file(self):
        return self.__pid_file

    def dump_default_config(self):
        log.diag("default config file(s)")
        for config_file in self.default_config_path:
            log.diag(config_file)

    def get_default_config(self):
        for config_file in self.default_config_path:
            if os.path.exists(config_file):
                return config_file
        return None

    def set_config(self, config_file):
        """
        set config file
        :param config_file:
        :return: None
        """
        '''
                 init      set_config
        case 1   None      None         => use default conf
        case 2   None      conf1        => use conf1
        case 3   conf1     None         => use conf1
        case 4   conf1     conf2        => use conf2
        '''

        self.need_reload_config = True
        if self.config_file is None:
            if config_file is None:
                log.event("use default config file")
                self.config_file = self.get_default_config()
                if self.config_file is None:
                    self.dump_default_config()
                    raise ConfigError(['exec'],
                                      'default config file does not exist')

            else:
                self.config_file = config_file
        else:
            if config_file is None:
                self.need_reload_config = False
                return
            else:
                self.config_file = config_file

    def startup(self):
        """
        This method is the entry point of starting this process up and do all
        what it wants to do. Hence, normally, developers overwrite this method
        to what they want.
        """

        '''
        # Children must inherit this.
        log.event('Starting...')
        while True:
            if self.TERMINATING:
                break
            time.sleep(1)
        log.event('Stopping...')
        '''

        raise NotImplementedError

    def stop(self):
        self.TERMINATING = True

    def shutdown_for_linux_service(self, secs_delay=10):
        """
        Shutdown this process. The parameter of secs_delay is the time, seconds,
        to wait for the termination status. If the process can't be terminated,
        after that seconds go by, shutdown() send a SIGKILL to do a force kill.
        """
        try:
            with open(self.__pid_file) as pid_file:
                pid = int(pid_file.read())
                system = '/proc/%s' % pid
        except:
            log.exception('Cannot read PID from pid_file: ', self.__pid_file)
            return False

        try:
            os.kill(pid, signal.SIGTERM)
        except Exception as e:
            if isinstance(e, OSError) and e.errno == errno.ESRCH:
                return True

            log.exception('Sent SIGTERM error.')
            return False

        # Delay check.
        startwatch = time.time()
        while True:
            if not os.path.exists(system):
                return True
            if time.time() - startwatch > secs_delay:
                break
            time.sleep(0.5)
        log.event("signal.SIGTERM fail to terminate process")

        # Last check.
        if os.path.exists(system):
            try:
                # Send SIGKILL to do a force termination.
                os.kill(pid, signal.SIGKILL)
            except Exception as e:
                if isinstance(e, OSError) and e.errno == errno.ESRCH:
                    return True

                log.exception('Sent SIGKILL error.')
                return False

        startwatch = time.time()
        while True:
            if not os.path.exists(system):
                return True
            if time.time() - startwatch > secs_delay:
                break
            time.sleep(0.5)

        return not os.path.exists(system)

    def lock_for_linux_service(self):
        """
        Lock this process via acquiring the lock of pid file. If this process
        will be a daemon process. daemonize() must be call prior to lock()
        since daemonize() will close all fd and, such that, the lock file
        will lost its lock acquisition from process.
        """
        try:
            self.__lock_file = lock_file = open(self.__pid_file, 'a+')
        except:
            log.exception('Cannot open pid file: ', self.__pid_file)
            return False

        try:
            fcntl.lockf(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except:
            log.exception('Cannot acquire lock of pid file: ', self.__pid_file)
            self.__lock_file.close()
            self.__lock_file = None
            return False

    def unlock_for_linux_service(self):
        """
        Unlock this process. After this call be made, the opened pid file
        will also be closed, and remove as well.
        """
        if self.__lock_file is None:
            return

        try:
            fcntl.lockf(self.__lock_file, fcntl.LOCK_UN)
            self.__lock_file.close()
            os.remove(self.__pid_file)
        except:
            # We don't care.
            pass

    def write_pid_for_linux_service(self):
        """
        Writes this process id to the pid, lock, file. If this process will
        be a daemon process, i.e. daemonize() will be also called, daemonize()
        must be called prior to write_pid(). It' because of daemonize() will
        change process ID.
        """
        if self.__lock_file is None:
            log.problem('PID file lock must be acquired prior to write PID.')
            return False

        try:
            self.__lock_file.seek(0)
            self.__lock_file.truncate()
            self.__lock_file.write(str(os.getpid()))
            self.__lock_file.flush()
            return True
        except:
            log.exception('Cannot write PID to file.')
            return False
