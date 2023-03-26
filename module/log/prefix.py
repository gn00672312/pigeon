from __future__ import print_function
import os
import sys

from . import utils
from .sink import LogSink
from .category import LogCategory



class LogPrefix(object):
    """
    Class regarding the prefix for each log message record.
    """
    # Define log prefix elements.
    PROCESS_NAME = 1 << 0
    PROCESS_ID   = 1 << 1
    DATETIME     = 1 << 2
    FILENAME     = 1 << 3
    LINENO       = 1 << 4


    # Type v.s. text mapping.
    _TEXT = {PROCESS_NAME: 'PROCESSNAME',
             PROCESS_ID:   'PROCESSID',
             DATETIME:     'DATETIME',
             FILENAME:     'FILENAME',
             LINENO:       'LINENO'}


    # Default prefix turned on for sinks.
    _options = {LogSink.STDERR: FILENAME | LINENO,
                LogSink.FILE: DATETIME | FILENAME | LINENO,
                LogSink.COLLECTIVE: PROCESS_NAME | PROCESS_ID |
                                    DATETIME | FILENAME | LINENO}


    @classmethod
    def prefix(cls, text):
        """
        Mapping the given prefix text to corresponding type.

        'text' must be a valid prefix text name.
        """
        text = text.upper()

        if text == cls._TEXT[cls.PROCESS_NAME]:
            return cls.PROCESS_NAME
        elif text == cls._TEXT[cls.PROCESS_ID]:
            return cls.PROCESS_ID
        elif text == cls._TEXT[cls.DATETIME]:
            return cls.DATETIME
        elif text == cls._TEXT[cls.FILENAME]:
            return cls.FILENAME
        else:
            # Must be line number.
            return cls.LINENO


    @classmethod
    def set(cls, prefix, sink, on):
        """
        Setting prefix for specific sink.
        """
        # Special case.
        # Collective sink always has datetime & process name & id on.
        must_on = cls.DATETIME | cls.PROCESS_NAME | cls.PROCESS_ID
        if sink == LogSink.COLLECTIVE and (prefix & must_on) and not on:
            print (("Warning: can't turn off datetime, process name,"
                    " or process id in the collective log."), file=sys.__stderr__)
            return

        # Special case.
        # Turn line number on only if file name is already on.
        # Turn line number off if file name turned off.
        filename_on = cls._options[sink] & cls.FILENAME
        if on and (prefix != cls.LINENO or filename_on):
            cls._options[sink] |= prefix
        else:
            cls._options[sink] &= (~prefix)
            if prefix == cls.FILENAME:
                cls._options[sink] &= (~cls.LINENO)


    @classmethod
    def text(cls, category, sink, datetime, filename, lineno, continuation):
        """
        Making a target prefix.
        """
        prefix = ''

        if sink == LogSink.COLLECTIVE or not continuation:
            prefix += '['

            # Process name.
            if cls._options[sink] & cls.PROCESS_NAME:
                prefix += utils.get_process_name()
                if cls._options[sink] & cls.PROCESS_ID:
                    prefix += '('
                else:
                    prefix += ' '

            # Process id.
            if cls._options[sink] & cls.PROCESS_ID:
                prefix += str(os.getpid())
                if cls._options[sink] & cls.PROCESS_NAME:
                    prefix += ')'
                prefix += ' '

            # Datetime.
            if cls._options[sink] & cls.DATETIME:
                prefix += utils.format_datetime(datetime)
                prefix += ' '

            # File name and line number.
            if cls._options[sink] & cls.FILENAME:
                prefix += filename

                if cls._options[sink] & cls.LINENO:
                    prefix += '(%s)' % lineno

                prefix += ' '

            # Category.
            prefix += LogCategory.text(category)

            # Keeps a space between prefix and message body.
            prefix +=  '] '

        return prefix
