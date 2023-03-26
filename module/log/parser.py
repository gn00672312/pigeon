from __future__ import print_function
import os
import re
import sys

from . import utils
from .sink import LogSink
from .filter import LogFilter
from .prefix import LogPrefix
from .category import LogCategory


class LogConfigParser(object):
    """
    Class to parse log configuration file.
    """
    # Configuration settings.
    LOG_CONFIG = ''
    LOG_DIR = LOG_NAME = ''
    COLLECTIVE_DIR = COLLECTIVE_NAME = ''
    LOG_BACKUP_COUNT = COLLECTIVE_BACKUP_COUNT = None

    # Backup count setting.
    _PATTERN_LOG_BACKUP_COUNT = re.compile(r'^LOG_BACKUP_COUNT\s*=\s*(\d+)$')

    _PATTERN_COLLECTIVE_BACKUP_COUNT = \
        re.compile(r'^COLLECTIVE_BACKUP_COUNT\s*=\s*(\d+)$')

    # LOG_DIR setting.
    _PATTERN_LOG_DIR = re.compile(r'^LOG_DIR\s*=\s*(\S+)$')

    # LOG_NAME setting.
    _PATTERN_LOG_NAME = re.compile(r'^LOG_NAME\s*=\s*(\S+)$')

    # COLLECTIVE_DIR setting.
    _PATTERN_COLLECTIVE_DIR = re.compile(r'^COLLECTIVE_DIR\s*=\s*(\S+)$')

    # COLLECTIVE_NAME setting.
    _PATTERN_COLLECTIVE_NAME = re.compile(r'^COLLECTIVE_NAME\s*=\s*(\S+)$')

    # Line pattern of a filter setting.
    _PATTERN_FILTER = re.compile(
        r'^(\S+)\s+'
        '(\S+)\s+'
        '(all|tty|file|collective)\s+'
        '(all|use|diag|event|problem|warning|bug|debug|verbose|report)\s*'
        '='
        '\s*(on|off)$',
        re.IGNORECASE)

    # Line pattern of a prefix setting.
    _PATTERN_PREFIX = re.compile(
        r'^(all|tty|file|collective)\s+'
        '(processname|processid|datetime|filename|lineno)\s*'
        '='
        '\s*(on|off)$',
        re.IGNORECASE)

    @classmethod
    def parse_log_config(cls):
        """
        Entrance of beginning parse log configuration file.
        """
        config_file = None

        # First priority: programmatically.
        if cls.LOG_CONFIG and os.path.isfile(cls.LOG_CONFIG):
            config_path = os.path.abspath(cls.LOG_CONFIG)
            try:
                config_file = open(config_path)
            except Exception:
                # We don't try any other possibilities. Just using defaults.
                return

        # Second priority: using environment variable.
        if config_file is None and os.getenv('LOG_CONFIG'):
            config_path = os.environ['LOG_CONFIG']
            try:
                config_file = open(config_path)
            except Exception as e:
                err = "Environment variable: LOG_CONFIG: %s: can't open: %s"
                print(err % (config_path, e), file=sys.__stderr__)

                # We don't try any other possibilities if an environment
                # variable is specified but can't parse in success.
                return

        if config_file is not None:
            LogConfigParser._parse(config_file)
            config_file.close()

    @classmethod
    def _parse(cls, config_file):
        """
        Parse the given opened config_file.
        """
        # Parse configuration file line by line.
        for lineno, line in enumerate(config_file, 1):
            setting = line.strip()

            # Comment line or empty.
            if setting.startswith('#') or not setting:
                continue

            # Trim inline comment.
            setting = setting.split('#', 1)[0]

            # LOG_BACKUP_COUNT line detection.
            mo = cls._PATTERN_LOG_BACKUP_COUNT.match(setting)
            if mo:
                cls.LOG_BACKUP_COUNT = int(mo.groups()[0])
                continue

            # COLLECTIVE_BACKUP_COUNT line detection.
            mo = cls._PATTERN_COLLECTIVE_BACKUP_COUNT.match(setting)
            if mo:
                cls.COLLECTIVE_BACKUP_COUNT = int(mo.groups()[0])
                continue

            # LOG_DIR line detection.
            mo = cls._PATTERN_LOG_DIR.match(setting)
            if mo:
                (cls.LOG_DIR,) = mo.groups()
                continue

            # LOG_NAME line detection.
            mo = cls._PATTERN_LOG_NAME.match(setting)
            if mo:
                (cls.LOG_NAME,) = mo.groups()
                continue

            # COLLECTIVE_DIR line detection.
            mo = cls._PATTERN_COLLECTIVE_DIR.match(setting)
            if mo:
                (cls.COLLECTIVE_DIR,) = mo.groups()
                continue

            # COLLECTIVE_NAME line detection.
            mo = cls._PATTERN_COLLECTIVE_NAME.match(setting)
            if mo:
                (cls.COLLECTIVE_NAME,) = mo.groups()
                continue

            # Filter line detection.
            mo = cls._PATTERN_FILTER.match(setting)
            if mo:
                process_name, src, sink_name, category_name, on = mo.groups()

                if sink_name.lower() == 'all':
                    cls._set_filter(process_name, src, LogSink.STDERR,
                                    category_name, on)
                    cls._set_filter(process_name, src, LogSink.FILE,
                                    category_name, on)
                    cls._set_filter(process_name, src, LogSink.COLLECTIVE,
                                    category_name, on)
                else:
                    sink = LogSink.sink(sink_name)
                    cls._set_filter(process_name, src, sink, category_name, on)

                continue

            # Prefix line detection.
            mo = cls._PATTERN_PREFIX.match(setting)
            if mo:
                sink_name, prefix_name, on = mo.groups()
                prefix = LogPrefix.prefix(prefix_name)
                on = on.lower() == 'on'

                if sink_name.lower() == 'all':
                    LogPrefix.set(prefix, LogSink.STDERR, on)
                    LogPrefix.set(prefix, LogSink.FILE, on)
                    LogPrefix.set(prefix, LogSink.COLLECTIVE, on)
                else:
                    sink = LogSink.sink(sink_name)
                    LogPrefix.set(prefix, sink, on)

                continue

            # Unrecognized setting line.
            err = 'Log config: %s: line %s: "%s": ignore malformed setting!'
            print(err % (config_file.name, lineno, setting), file=sys.__stderr__)

    @classmethod
    def _set_filter(cls, process_name, source, sink, category_name, on):
        """
        Set specified filter.
        """
        on = on.lower() == 'on'

        if category_name.lower() == 'all':
            LogFilter.set(utils.get_process_name(), process_name,
                          source, sink, LogCategory.USE, on)
            LogFilter.set(utils.get_process_name(), process_name,
                          source, sink, LogCategory.DIAG, on)
            LogFilter.set(utils.get_process_name(), process_name,
                          source, sink, LogCategory.EVENT, on)
            LogFilter.set(utils.get_process_name(), process_name,
                          source, sink, LogCategory.PROBLEM, on)
            LogFilter.set(utils.get_process_name(), process_name,
                          source, sink, LogCategory.WARNING, on)
            LogFilter.set(utils.get_process_name(), process_name,
                          source, sink, LogCategory.BUG, on)
            LogFilter.set(utils.get_process_name(), process_name,
                          source, sink, LogCategory.DEBUG, on)
            LogFilter.set(utils.get_process_name(), process_name,
                          source, sink, LogCategory.VERBOSE, on)
        else:
            category = LogCategory.category(category_name)
            LogFilter.set(utils.get_process_name(), process_name,
                          source, sink, category, on)
