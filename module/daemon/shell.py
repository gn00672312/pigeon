# -*- coding: utf-8 -*-
import errno
import select
from subprocess import Popen, PIPE
from datetime import datetime, timedelta
import platform

try:
    from subprocess import TimeoutExpired
except:
    """under python 3.3"""

WINDOWS_PLATFORM = platform.system() == "Windows"

#
# lwsu@2018-03-31
# one day should be enough
#
DEFAULT_TIMEOUT = 60 * 60 * 24


class Shell(object):
    """
    A class to wrap up, and simplify, the usage of Python subprocess module.

    To execute external commands, simply do:
      - Use run() with proper parameters to execute a external command.
      - Use wait() to block caller process, the synchronous way, until callee
        termination. Or, the asynchronous way, use done() to check if callee
        is finished.
      - Use pid, read only property, to acquire callee's PID.
      - Use returncode, read only property, to acquire callee's return code.
      - Use stdout, read only property, to acquire callee's standard output
        messages.
      - Use stderr, read only property, to acquire callee's standard error
        message.
    """

    def __init__(self, timeout=DEFAULT_TIMEOUT):
        self.__pid = None
        self.__cmd = None
        self.__stdout = None
        self.__stderr = None
        self.__returncode = None
        self.__subprocess = None
        self.__begin_time = None

        # if timeout is 0, assign None
        # subprocess.communicate timeout argument can't use 0, must None
        self.__timeout = timeout if timeout else None

    def __str__(self):
        s = "cmd=[%s], pid=%s" % (self.__cmd, self.__pid)
        if self.__returncode is None:
            s += "."
        else:
            s += ", returncode=%s" % self.__returncode
            s += ", stdout=[%s]" % self.__stdout
            s += ", stderr=[%s]." % self.__stderr
        return s

    @property
    def pid(self):
        return self.__pid

    @property
    def cmd(self):
        if isinstance(self.__cmd, bytes):
            return self.__cmd.decode("utf-8")
        else:
            return self.__cmd

    @property
    def stdout(self):
        if isinstance(self.__stdout, bytes):
            return self.__stdout.decode("utf-8")
        else:
            return self.__stdout

    @property
    def stderr(self):
        if isinstance(self.__stderr, bytes):
            return self.__stderr.decode("utf-8")
        else:
            return self.__stderr

    @property
    def returncode(self):
        return self.__returncode

    def run(self, *args, **kws):
        """
        Execute external command.

        The parameter args is the command string you want to execute. You can
        make up a full command string or, instead, separate the command itself
        and parameters into parameters. In the latter case, a full command
        string will be made internally for you.

        The parameter kws is a keyword arguments you want to place into
        subprocess.Popen to get better control on it.
        """
        self.__cmd = self.__pid = self.__returncode = None
        self.__stdout = self.__stderr = None

        self.__cmd = ' '.join([str(i) for i in args])
        if WINDOWS_PLATFORM:
            close_fds = False
        else:
            close_fds = True
        self.__subprocess = Popen(self.__cmd, shell=True, stdout=PIPE,
                                  stderr=PIPE, close_fds=close_fds, **kws)
        self.__pid = self.__subprocess.pid
        self.__begin_time = datetime.now()

        return self

    def wait(self):
        """
        Block, the synchronous way, caller until callee termination.
        """
        if self.__returncode is None:
            stdout, stderr = self.__communicate()
            self.__stdout = stdout.strip()
            self.__stderr = stderr.strip()
            self.__returncode = self.__subprocess.returncode
        return self

    def done(self):
        """
        The asynchronous way to check whether callee is finished.
        """
        if self.__subprocess is None:
            return None
        if self.__returncode is not None:
            return True

        self.__kill_if_timeout()

        # Not yet. Query its status.
        self.__returncode = self.__subprocess.poll()
        if self.__returncode is None:
            return False

        stdout, stderr = self.__communicate()

        self.__stdout = stdout.strip()
        self.__stderr = stderr.strip()
        return True

    def __communicate(self):
        try:
            # subprocess.communicate timeout argument is added after python 3.3,
            # try to use the TimeoutExpired in runtime python version.
            TimeoutExpired
            while True:
                try:
                    return self.__subprocess.communicate(timeout=self.__timeout)
                except TimeoutExpired:
                    self.__subprocess.kill()
                    return self.__subprocess.communicate()
                except select.error as no:
                    if no != errno.EINTR:
                        raise

        except NameError as err:
            while True:
                try:
                    return self.__subprocess.communicate()
                except select.error as no:
                    if no != errno.EINTR:
                        raise
                    else:
                        self.__kill_if_timeout()

    def __kill_if_timeout(self):
        if self.__begin_time and self.__timeout > 0:
            spend_time = datetime.now() - self.__begin_time
            if spend_time.total_seconds() > self.__timeout:
                self.kill()

    def kill(self):
        if self.__subprocess is not None:
            self.__subprocess.kill()
