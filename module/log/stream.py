# -*- coding: utf-8 -*-
from __future__ import print_function
import os
import re
import sys
import types
import datetime
import threading
import pytz

from . import utils
from .sink import LogSink
from .prefix import LogPrefix
from .filter import LogFilter
from .category import LogCategory
from .parser import LogConfigParser

LOG_TZ = os.getenv('LOG_TZ')


class LastLogInfo:
    """
    Class to process duplicate log messages.
    """
    # Format to dump duplicate messages.
    _MSG_REPEAT = 'Last message repeated %s time(s).'

    def __init__(self):
        self._msg = ''
        self._prefix = ''
        self._category = 0
        self._num_repeat = 0

    def is_duplicate(self, category, msg):
        """
        Duplicate message is determined by both category and message.
        """
        return category == self._category and msg == self._msg

    def dump_to(self, stream):
        """
        Dump duplicate messages onto specified stream.
        """
        if self._num_repeat > 0:
            msg = self._MSG_REPEAT % self._num_repeat
            stream.write(self._prefix + msg + os.linesep)

            self._msg = ''
            self._prefix = ''
            self._category = 0
            self._num_repeat = 0

    def keep(self, category, prefix, msg):
        """
        Keeps the given category, prefix, and msg as last one.
        """
        self._category = category
        self._prefix = prefix

        if msg == self._msg:
            self._num_repeat += 1
        else:
            self._msg = msg
            self._num_repeat = 0


class LogStream(object):
    """
    Class operates log stream.
    """
    # Programmatically settings.
    log_dir = log_name = ''
    collective_dir = collective_name = ''
    log_backup_count = collective_backup_count = None

    # For log purge.
    _log_backup_count = 7
    _log_filename_prefix = ''
    _log_filename_want_pid = False
    _log_filename_pattern = re.compile(r'.+\.\d{4}-\d{2}-\d{2}\.\d+\.log$')

    _collective_backup_count = 7
    _collective_filename_prefix = ''
    _collective_filename_pattern = re.compile(r'.+\.\d{4}-\d{2}-\d{2}\.log$')

    # Initialized indicator.
    _initialized = False

    # For thread-safety.
    _lock = threading.RLock()

    # For file breaking.
    _last_break = None
    _break_at_midnight = True

    # Message streams.
    _file = None
    _collective = None

    # Flag of breaking log.
    _break_file_requested = True
    _break_collective_requested = True

    # For duplicate messages.
    _last = {LogSink.STDERR: LastLogInfo(),
             LogSink.FILE: LastLogInfo(),
             LogSink.COLLECTIVE: LastLogInfo()}

    # Ingredients to make a log record.
    _lineno = None
    _filename = None
    _datetime = None
    _category = None
    _continuation = False

    # Filter for the current log record.
    _filter = None

    @classmethod
    def lock_out_other_threads(cls, activate):
        """
        Class method to acquire or release internal thread lock.
        """
        if activate:
            cls._lock.acquire()
        else:
            cls._lock.release()

    @classmethod
    def set_auto_break_at_midnight(cls, enabled):
        """
        Class method to set automation of breaking log file at midnight.
        """
        cls._break_at_midnight = enabled

    @classmethod
    def break_log_file(cls):
        """
        Class method to manually break log file.
        """
        cls._break_file_requested = True
        cls._break_collective_requested = True

    @classmethod
    def suppressed(cls, category, filename, lineno, continuation):
        """
        Class method to check if we should suppress this log message
        based on the give parameters.
        """
        if not cls._initialized:
            cls._initialize()

        cls._filter = LogFilter(category, filename)
        suppressed = cls._filter.suppress()

        if not suppressed:
            filename = os.path.splitext(filename)[0]
            filename = filename.replace(os.sep, '.')

            cls._lineno = lineno
            cls._filename = filename
            cls._category = category
            cls._continuation = continuation
            if LOG_TZ:
                cls._datetime = datetime.datetime.utcnow().replace(tzinfo=pytz.UTC)
                cls._datetime = cls._datetime.astimezone(pytz.timezone(LOG_TZ))
            else:
                cls._datetime = datetime.datetime.now()

        return suppressed

    @classmethod
    def sink_msg(cls, msg):
        """
        Class method to emit the given msg to sinks.
        """
        if not msg:
            return

        # Check file breaking condition first.
        cls._check_break()

        # File sink.
        if cls._filter.log_to(LogSink.FILE):
            if cls._break_file_requested:
                cls._close(for_collective=False)
                cls._break_file_requested = False
                cls._open(for_collective=False)
                cls._purge(for_collective=False)
            cls._write(cls._file, LogSink.FILE, msg)

        # Collective sink.
        if cls._filter.log_to(LogSink.COLLECTIVE):
            if cls._break_collective_requested:
                cls._close(for_collective=True)
                cls._break_collective_requested = False
                cls._open(for_collective=True)
                cls._purge(for_collective=True)

            # For collective file, process-safe is mandatory.
            if cls._collective is not None:
                lock = utils.LogFileLock(cls._collective)
                if lock.got_lock():
                    cls._write(cls._collective, LogSink.COLLECTIVE, msg)

        # Standard error.
        if sys.__stderr__:
            try:
                is_a_tty = sys.__stderr__.isatty()
            except:
                is_a_tty = False
            if is_a_tty and cls._filter.log_to(LogSink.STDERR):
                encoding = sys.__stderr__.encoding
                if encoding and encoding.lower() != 'utf-8':
                    __codes = ['utf-8', 'big5']
                    for __code in __codes:
                        try:
                            msg = msg.decode(__code)
                            break
                        except:
                            pass

                    msg = msg.encode(encoding)
                RED = '\033[0;31m'
                NC = '\033[0m'  # No Color
                if cls._category in (LogCategory.PROBLEM,
                                     LogCategory.WARNING, LogCategory.BUG):
                    msg = RED + msg + NC
                cls._write(sys.__stderr__, LogSink.STDERR, msg)

    @classmethod
    def _write(cls, stream, sink, msg):
        """
        Internal class method to write log message to the given stream.
        """
        if not msg:
            return

        # Check end of line.
        # bytes and str can't combine in python3
        if isinstance(msg, bytes):
            linesep = os.linesep.encode()
        else:
            linesep = os.linesep

        if not msg.endswith(linesep):
            msg += linesep

        # Make prefix.
        prefix = LogPrefix.text(cls._category, sink, cls._datetime,
                                cls._filename, cls._lineno, cls._continuation)

        # Get last message info.
        last = cls._last[sink]
        is_duplicate = last.is_duplicate(cls._category, msg)

        # Force log the USE category message.
        if (cls._category == LogCategory.USE) or (not is_duplicate):
            last.dump_to(stream)

            # Write out current one.
            try:
                stream.write(prefix + msg)
            except:
                stream.write("Exception : " + prefix)

            if sink != LogSink.STDERR:
                # Force dumping message to disk file
                # avoiding process crash.
                stream.flush()
                os.fsync(stream.fileno())

        # Keeps current one as the new last if non-USE.
        if cls._category != LogCategory.USE:
            last.keep(cls._category, prefix, msg)

    @classmethod
    def _open(cls, for_collective):
        """
        Class method to open log file either process mode or collective mode.
        """
        log_path = cls._get_file_path(for_collective)
        if not log_path:
            return

        try:
            stream = open(log_path, 'a')
        except Exception as e:
            err = "Can't open log file: %s: %s"
            print(err % (log_path, e), file=sys.__stderr__)
            return

        if for_collective:
            cls._collective = stream
        else:
            cls._file = stream

    @classmethod
    def _close(cls, for_collective):
        """
        Class method to close log file either process mode or collective mode.
        """
        sink = LogSink.COLLECTIVE if for_collective else LogSink.FILE
        stream = cls._collective if for_collective else cls._file

        # Check duplicate message.
        if stream is not None:
            cls._last[sink].dump_to(stream)
            stream.close()

            if for_collective:
                cls._collective = None
            else:
                cls._file = None

    @classmethod
    def _purge(cls, for_collective):
        """
        Class method to purge either process log or collective log.
        """
        if for_collective:
            count = cls._collective_backup_count
            prefix = cls._collective_filename_prefix
            pattern = cls._collective_filename_pattern
        else:
            count = cls._log_backup_count
            prefix = cls._log_filename_prefix
            pattern = cls._log_filename_pattern

        # Backup count must be > 0.
        if count <= 0:
            return

        # Find out candidates.
        dir_name = os.path.dirname(prefix)
        day_to_keep = cls._last_break - datetime.timedelta(days=count)

        for filename in os.listdir(dir_name):
            mo = pattern.match(filename)
            if mo:
                # Parse datetime.
                try:
                    file_datetime = datetime.datetime.strptime(mo.groups()[0],
                                                               '%Y-%m-%d')
                    if file_datetime.date() < day_to_keep:
                        os.remove(os.path.join(dir_name, filename))
                except Exception:
                    continue

    @classmethod
    def _determine_log_info(cls):
        """
        Determine information regarding process log if not determined yet.
        """
        if cls._log_filename_prefix:
            return

        # adjust priority
        _dir = cls.log_dir or \
               LogConfigParser.LOG_DIR or \
               os.getenv('LOG_DIR') or os.getcwd()

        if not os.path.isabs(_dir):
            _dir = os.path.abspath(_dir)

        # adjust priority
        _name = cls.log_name or \
                LogConfigParser.LOG_NAME or \
                os.getenv('LOG_NAME')

        if _name:
            cls._log_filename_want_pid = False
            cls._log_filename_prefix = os.path.join(_dir, _name)
            cls._log_filename_pattern = re.compile(
                r'.+\.(\d{4}-\d{2}-\d{2})\.log$')
        else:
            _name = utils.get_process_name()
            cls._log_filename_want_pid = True
            cls._log_filename_prefix = os.path.join(_dir, _name)
            cls._log_filename_pattern = re.compile(
                r'.+\.(\d{4}-\d{2}-\d{2})\.\d+\.log$')

        _count = cls._log_backup_count
        if os.getenv('LOG_BACKUP_COUNT', '').isdigit():
            _count = int(os.getenv('LOG_BACKUP_COUNT'))
        elif isinstance(LogConfigParser.LOG_BACKUP_COUNT, int):
            _count = LogConfigParser.LOG_BACKUP_COUNT
        elif isinstance(cls.log_backup_count, int):
            _count = cls.log_backup_count

        cls._log_backup_count = _count
        if cls._log_backup_count < 0:
            cls._log_backup_count = 0

    @classmethod
    def _determine_collective_info(cls):
        """
        Determine information regarding collective log if not determined yet.
        """
        if cls._collective_filename_prefix:
            return

        # adjust priority
        _dir = cls.collective_dir or \
               LogConfigParser.COLLECTIVE_DIR or \
               os.getenv('COLLECTIVE_DIR') or \
               os.getcwd()

        if not os.path.isabs(_dir):
            _dir = os.path.abspath(_dir)

        # adjust priority
        _name = cls.collective_name or \
                LogConfigParser.COLLECTIVE_NAME or \
                os.getenv('COLLECTIVE_NAME') or \
                utils.get_process_name()

        cls._collective_filename_prefix = os.path.join(_dir, _name)
        cls._collective_filename_pattern = re.compile(
            r'.+\.(\d{4}-\d{2}-\d{2})\.log$')

        _count = cls._collective_backup_count
        if os.getenv('COLLECTIVE_BACKUP_COUNT', '').isdigit():
            _count = int(os.getenv('COLLECTIVE_BACKUP_COUNT'))
        elif isinstance(LogConfigParser.COLLECTIVE_BACKUP_COUNT, int):
            _count = LogConfigParser.COLLECTIVE_BACKUP_COUNT
        elif isinstance(cls.log_backup_count, int):
            _count = cls.log_backup_count

        cls._collective_backup_count = _count
        if cls._collective_backup_count < 0:
            cls._collective_backup_count = 0

    @classmethod
    def _get_file_path(cls, for_collective, create_dir=True):
        """
        Class method to get log file path either process mode
        or collective mode.
        """
        if for_collective:
            cls._determine_collective_info()
            full_path = cls._collective_filename_prefix
        else:
            cls._determine_log_info()
            full_path = cls._log_filename_prefix

        # Make final version.
        if LOG_TZ:
            # 這個要用與 log 相同的 time zone 去比對
            today = datetime.datetime.utcnow().replace(tzinfo=pytz.UTC)
            today = today.astimezone(pytz.timezone(LOG_TZ))
        else:
            today = datetime.datetime.now()

        full_path += today.strftime('.%Y-%m-%d')

        if (not for_collective) and cls._log_filename_want_pid:
            full_path += '.%s' % os.getpid()

        full_path += '.log'

        # Create directory if need.
        if create_dir:
            dir_path = os.path.dirname(full_path)
            try:
                os.makedirs(dir_path, mode=0o755)
            except Exception as e:
                if not os.path.exists(dir_path):
                    print(e, file=sys.__stderr__)
                    full_path = None

        return full_path

    @classmethod
    def _initialize(cls):
        """
        Class method does initializations.
        """
        cls._initialized = True
        LogConfigParser.parse_log_config()

    @classmethod
    def _check_break(cls):
        """
        Class method to check if we should break log automatically.
        """
        if cls._break_at_midnight:
            today = datetime.date.today()
            if today != cls._last_break:
                cls.break_log_file()
                cls._last_break = today
