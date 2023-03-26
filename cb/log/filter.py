import os
import copy

from .sink import LogSink
from .category import LogCategory


class DefaultSwitch(object):
    """
    A class functions as a structure in C/C++.
    """
    def __init__(self):
        self.collective = 0
        self.tty = ~(LogCategory.DEBUG | LogCategory.VERBOSE)
        self.file = ~(LogCategory.DEBUG | LogCategory.VERBOSE)



class LogFilter(object):
    """
    Class to maintain a process-wide filtering.
    """
    # Default switch.
    _default_switch = DefaultSwitch()

    # Dictionary of mapping source to switch.
    _src_2_switch = {}


    def __init__(self, category, filename):
        # Try full module path first. (More specific)
        module_path = os.path.normcase(os.path.splitext(filename)[0])
        module_path = module_path.replace(os.sep, '.')
        switch = LogFilter._src_2_switch.get(module_path, None)

        # Try base file name, then.
        if not switch:
            py_name = os.path.basename(filename)
            switch = LogFilter._src_2_switch.get(py_name, self._default_switch)

        self._log_to_sink = {
            LogSink.STDERR: bool(switch.tty & category),
            LogSink.FILE: bool(switch.file & category),
            LogSink.COLLECTIVE: bool(switch.collective & category)}


    def log_to(self, sink):
        """
        Return the corresponding switch for the given sink.
        """
        return self._log_to_sink[sink]


    def suppress(self):
        """
        Return if we should suppress logging messages.
        """
        for sink in range(LogSink.NUM_SINKS):
            if self._log_to_sink[sink]:
                return False
        return True


    @classmethod
    def set(cls, this_process, process_name, source, sink, category, on):
        """
        Set filter for specified source, sink, and category as well.
        """
        this_process = os.path.normcase(this_process)
        process_name = os.path.normcase(process_name)

        if process_name != this_process and process_name.lower() != 'all':
            return

        if source.lower() == 'all':
            switch = cls._default_switch
            cls._update_switch(switch, sink, category, on)

            for the_source, the_switch in cls._src_2_switch.items():
                cls._update_switch(the_switch, sink, category, on)
                cls._src_2_switch[the_source] = the_switch
        else:
            source = os.path.normcase(source)
            default_switch = copy.deepcopy(cls._default_switch)
            new_switch = cls._src_2_switch.get(source, default_switch)
            the_switch = new_switch

            cls._update_switch(the_switch, sink, category, on)
            cls._src_2_switch[source] = new_switch


    @classmethod
    def _update_switch(cls, switch, sink, category, on):
        """
        Update the given 'switch' per providing sink and category.
        """
        if sink == LogSink.STDERR:
            switch.tty = cls._twiddle_bit(switch.tty, category, on)
        elif sink == LogSink.FILE:
            switch.file = cls._twiddle_bit(switch.file, category, on)
        elif sink == LogSink.COLLECTIVE:
            switch.collective = cls._twiddle_bit(switch.collective,
                                                  category, on)


    @classmethod
    def _twiddle_bit(cls, bits, mask, on):
        """
        Bit operations.
        """
        if on:
            return bits | mask
        else:
            return bits & (~mask)
