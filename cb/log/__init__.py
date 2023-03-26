"""
                                      Log
                    The Enhanced Logging Package for Python
                   =========================================
                               Author: CloudyBay
                            Last Update: 2016-12-23



Introduction
------------
    'log', just like its name, is a logging package designing for Python
    development language. It lets a programmer easily re-direct log messages
    to various sinks. It is thread-safe as well as process-safe. Accordingly,
    it can be used not only in a multi-threaded but also in a multi-process
    environment. Though Python is a cross-platform development language, 'log'
    package only supports, and tests, on Windows and Linux so far. But MAC OS
    platform should work properly, just my guess.



Usage
-----
    To use 'log' package, simply import 'log' package. Then use the public
    interfaces to generate a proper message with corresponding category.
    A simplest example with minimum code is listed below:

        File: test.py

            import log
            log.event('This is an event message!')


    There should be now a log file named test.{date}.{pid}.log generated
    under current working directory. {pid} is the process id you launched the
    process, while {date} is the date in yyyy-mm-dd format. The file content
    looks like the following:

        [2011-12-08 11:31:07,489 test.py(4) EVENT] This is an event message!


    As you can see, the message had been wrote to the log file with some
    additional content bracketed by [ and ]. 'log' named that content 'prefix'.
    It contains 3 parts:


    *** Message datetime
        The content of '2011-12-08 11:31:07,489'.


    *** Message originator
        The content of 'test.py(4)'. 'test.py' is the file name fires the
        message while '4' indicates the line number.


    *** Message category.
        The content of 'EVENT'. It's generated due to you made a call to
        event() interface. You can, of course, generate other category messages
        via making calls to other interfaces. For instance, problem() would
        generate a 'PROBLEM' category message.



Message Category
----------------
    Many logging packages, including Python's builtin logging, use the idea of
    level to distinguish messages. 'log' does not follow that. Instead, 'log'
    uses category as its main concept to classify messages. There are 9
    categories available in 'log' package, they are:


    *** Use
        Generates 'USE' in prefix via use() interface.

        This category should be used only in a GUI environment. The existence
        of this category is to trace the usage of widgets as well as operation
        flow for users.


    *** Diagnostic
        Generates 'DIAG' in prefix via diag() interface.

        A diagnostic message can be used in order to diagnose something you are
        interesting. For example, to diagnose the working directory once the
        program starts up, you can generate a diagnostic message with the
        current working directory as the main message body.

        If you need to generate a diagnostic message without prefix, using _()
        interface can achieve this goal. But note that using _() to generate a
        diagnostic message without prefix only work for process sink only.


    *** Event
        Generates 'EVENT' in prefix via event() interface.

        A regular event message. For example, if a socket client program wants
        to connect to a socket server, you can generate an event message once
        the connection established.


    *** Problem
        Generates 'PROBLEM' in prefix via problem() interface.

        Indicate an error message. If a daemon process (a service on Windows),
        for example, cannot connect to a database server. You can terminate it,
        or better generate a problem  message periodically till the connection
        is established.

        There's another interface can generate such category message. It is
        exception(). Like its name, exception() must be used only in a place
        may receive an exception. That is, you should use exception() only
        under a block of except clause. The only one difference between them
        is that exception() not only generate the message from parameters but
        also emit exception trackback information.


    *** Warning
        Generates 'WARNING' in prefix via warning() interface.

        Another familiar message to programmers.


    *** Bug
        Generates 'BUG' in prefix via bug() interface.

        You should use this category to indicate a programming bug. Nothing is
        easier, to explain you, than providing an example code.

            import log
            import types

            def connect_to(server_name):
                if type(server_name) != types.StringType:
                    log.bug('server name must be a string!')
                do_connect(server_name)


    *** Debug
        Generates 'DEBUG' in prefix via debug() interface.

        The most familiar message to programmers. Note that this category
        message is turned off by default.


    *** Verbose
        Generates 'VERBOSE' in prefix via verbose() interface.

        A detailed message. Note that this category message is turned off
        by default.



Message Sink
------------
    A sink, in 'log', is a destination the log messages writes to. In Python's
    builtin logging package, it's called 'handler'. Currently, 'log' provides
    3 sinks for programming using:


    *** TTY (a.k.a. standard error)
        TTY is a terminology and represents the standard error device. We can
        say, therefore, that the tty is a terminal device on Linux, while it
        is a DOS command prompt window on Windows.

        By default, 'log' will generate all categories except both debug and
        verbose. Moreover, messages to a tty only have filename and line number
        as their prefix.


    *** Process file
        In 'log', a process file is a process-dependent log file. So, each
        process owns a log file to keep all messages originated from itself.

        By default, 'log' generate all categories except both debug and
        verbose. And the messages to a process file have datetime, filename,
        and line number as their prefix.

        Each process can vary its process file path via making a modification
        to either LOG_DIR or LOG_NAME environment variable. Also, you can
        direct sets that environment variable as long as it occurs prior to
        the very first category interface be called.

        More care should be taken here that if there are more than one process
        has the same full path for their process log file, it could mess up the
        messages in that process log file. In such, use collective log file.


    *** Collective file
        In addition to tty and process log file, 'log' provides another special
        file: collective log file. A collective log file is used for keeping
        all messages originated from multiple process. For that reason, before
        writing messages to a collective file, 'log' acquires a cross-process
        file lock to avoid messing up the messages.

        By default, 'log' generate no category to collective files. That is,
        turning collective log files off is the default behavior. And 'log'
        uses all parts, including process name, process id, datetime,
        file name, and line number, as its default prefix.

        Programs can vary their collective file path via making a modification
        to either COLLECTIVE_DIR or COLLECTIVE_NAME environment variable. Also,
        like process file, you can direct sets that environment variable as
        long as it occurs prior to the very first category interface be called.



Message Prefix
--------------
    Before writing log messages to sinks, no matter which category interface
    you use, 'log' attaches some additional information to the original
    messages as its preliminary. 'log' named the preliminary information as
    prefix.


    The message prefix is a combination of, in order, at most, process name,
    process identifier, date and time, source file name, line number, and
    category symbol. Nevertheless, it is bracketed by a pair of square
    brackets. A completed prefix should looks like the following:

        [test(2584) 2009-05-20 14:23:57,003 test.py(23) EVENT]


    You may ask that can I suppress a prefix be generated for some specific
    purpose. The answer is yes. As we mentioned above, using _() interface
    (notice the underscore) is the only one possibility to achieve that.


    Again, this works for only process log file. And the message prefix is
    automatically generated by 'log'. You, the programmer, should write nothing
    but the original message body.



Customization
-------------
    Many behaviors in 'log' package can be customized via either environment
    variables or a configuration file.


    Environment Variables
    ---------------------
        There are 4 environment variables available in 'log'. They are:


        *** LOG_CONFIG
            This environment variable guides 'log' where the configuration
            file exists. If none such environment variable specified, 'log'
            tries to use a file named "log.conf", under current working
            directory, if it exists there and can be accessed by 'log'.
            Otherwise, 'log' won't use a configuration file and all behaviors
            will use its defaults.


        *** LOG_DIR
            This environment variable indicates the directory process logs
            reside. You don't need to create it in your code, 'log' create
            it for you on demand.


        *** LOG_NAME
            This environment variable tells 'log' the name of the process log
            file will be created. If this environment variable is not
            specified, 'log' will use {process_name}.{date}.{pid}.log as the
            default value.


        *** LOG_BACKUP_COUNT
            This environment variable tells 'log' how many days process log
            wants to keep. If it's 0 (or < 0), 'log' won't purge any process
            log file.


        *** COLLECTIVE_DIR
            Like LOG_DIR, this environment variable indicates the directory
            collective logs reside. Also, you don't need to manually create
            it in your code, 'log' crate it for you on demand.


        *** COLLECTIVE_NAME
            Like LOG_NAME, this environment variable tells 'log' the name of
            collective log file will be created. If this environment variable
            is not specified, 'log' will use {process_name}.{date}.log as the
            default value.


        *** COLLECTIVE_BACKUP_COUNT
            Like LOG_BACKUP_COUNT, this environment variable tells 'log' how
            many days collective log wants to keep. If it's 0 (or < 0), 'log'
            won't purge any collective log file.



    Log Configuration
    -----------------
        A configuration file in 'log' package can determine what a message
        looks like and where it goes to. Besides it can set where the log files
        will be generated and what the name is. Remember that each line can
        contain only a setting.


        There are 3 ways to tell 'log' where the configuration should be used.
        They are, in priority, listed below:

        (1) LOG_CONFIG environment.
        (2) A file named 'log.conf' under current working directory.
        (3) Uses set_log_config() public interface.


        Like Linux shell script, '#' character begins a comment from there and
        till the end of line. Any viewable space, including ' ' and '\t', can
        be used as the delimiter to separate each token. Moreover, most text is
        case-insensitive except 1) an exactly process name on case-sensitive
        platform, 2) an exactly source file name on case-sensitive platforms,
        and 3) file path relevant settings.


        *** File relevant settings
            These settings have <key> = <value> format. The key part is
            case-sensitive and only 6 names are allowed: LOG_DIR, LOG_NAME,
            LOG_BACKUP_COUNT, COLLECTIVE_DIR, COLLECTIVE_NAME, and
            COLLECTIVE_BACKUP_COUNT. The value part can't have any space in it
            and case-sensitivity depends on O.S. platform. Example is listed
            below:

                LOG_DIR = the_dir_to_populate_process_log
                LOG_NAME = the_name_of_process_log
                LOG_BACKUP_COUNT = 3

                COLLECTIVE_DIR = the_dir_to_populate_collective_log
                COLLECTIVE_NAME = the_name_of_collective_log
                COLLECTIVE_BACKUP_COUNT = 3


        *** Filter settings
            A filter line is composed of, in order, process name, source file
            name, sink name, category name, a '=' sign, and either 'on' or
            'off'. The first four tokens can be replaced by 'all' to imply
            every one. For the example of

                all  all  all  all = off
                all  all  tty  problem = on

            The first line turns messages off for all processes, all source
            files, all sinks, and all categories. The second line indicates
            that a message belongs to problem category should go to the process
            attached tty device. No matter which the process and source file it
            originates from.

            For sink name, 'tty' represents a terminal device, 'file'
            represents the process log file, and 'collective' represents the
            collective log file.

            For category name, string in lower (or upper) cases represents its
            corresponding category but 'diag' represents a diagnostic message.

            If there's no configuration file exists or there's no filter
            settings available in configuration file, 'log' turns all messages
            on by default, except debug and verbose categories for tty and
            process log. And turns everything off for collective log.


        *** Prefix setting
            A prefix line is composed of, in order, sink name, prefix type,
            a '=' sign, and either 'on' or 'off'. The sink name can be replaced
            by 'all' to imply every one, while the prefix type can only be,
            case-insensitive, 'processName', 'processId', 'datetime',
            'fileName', or 'lineNo'. That is, you cannot use 'all' to imply
            every one.

            By default, 'log' turns source file name and line number on for tty
            (standard error) log; turns datetime, source file name, and line
            number on for process log; turns everything (including process
            name, process id, datetime, source file name, and line number) on
            for collective log. Note that 'log' doesn't permit you to turn
            datetime and process name off for collective log. Moreover, 'log'
            will turns line number off automatically if you turn source file
            name off.

            There is no way to suppress the prefix generation unless using _()
            interface if that message got one sink to go. Even you turn all
            prefix types off in the configuration file, still the message
            category will show in the prefix.



    Precedence
    ----------
        'log' provides programmers to customize its behaviors in many ways, but
        environment variables always got the first priority. Here are the
        precedence, in descending order.

        (1) Environment variable.
        (2) Configuration file.
        (3) Programmatically.



Public Interfaces
-----------------
    'log' privides the following public interfaces:


    *** use(*args)
    *** diag(*args)
    *** event(*args)
    *** problem(*args)
    *** warning(*args)
    *** bug(*args)
    *** debug(*args)
    *** verbose(*args)
    *** exception(*args)
    *** _(*args)
        They are used to generated 'USE', 'DIAG', 'EVENT', 'PROBLEM',
        'WARNING', 'BUG', 'DEBUG', 'VERBOSE', 'PROBLEM', and 'DIAG' category
        messages correspondingly.

        All interfaces above take variable arguments. All arguments will be
        converted to string format no matter what type they are. For example
        of normal usage:

            for i in range(10):
                log.debug('In for loop: %i', i)
                # Do something here.

        By means of 'log' you have another handy way:

            for i in range(10):
                log.debug('In for loop: ', i)
                # Do something here.

        In line 2, 'log' automatically convert the integer, variable i, to its
        corresponding string format via str() builtin function. You don't need
        to do yourself like the first example shows. That mechanism can be
        applied to all kinds of python objects.

        Please refer to chapter 'Message Category' for more details.


    *** set_auto_break_at_midnight(enabled=True)
        Normally you don't need to call this interface. 'log' breaks at
        midnight automatically. But you can turn this feature off manually.


    *** break_log_file()
        Normally you don't need to call this interface. 'log' would break
        automatically for you. But you can call this interface to break
        manually on demand.


    *** set_log_config(config_path)
    *** set_log_dir(log_dir)
    *** set_log_name(log_name)
    *** set_log_backup_count(value)
    *** set_collective_dir(collective_dir)
    *** set_collective_name(collective_name)
    *** set_collective_backup_count(value)
        They function like environment variables 'LOG_CONFIG', 'LOG_DIR',
        'LOG_NAME', 'LOG_BACKUP_COUNT', 'COLLECTIVE_DIR', 'COLLECTIVE_NAME',
        and 'COLLECTIVE_BACKUP_COUNT' correspondingly. Remind you again that
        these interfaces always got the lowest priority in precedence.



File Breaking
-------------
    Log breaking, also known as log rotating, is an action to close the log
    file and open a new one. 'log' only supports daily breaking at midnight
    currently. I hope 'log' can support sized breaking in the near future.



Programming Notes
-----------------
    'log' package works on only Python2 with version 2.6 and newer platform.
    Python version 3 may be supported, just maybe, I never give it a try.
"""
import os
import sys
import inspect
try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO

import traceback

from .stream import LogStream

from .category import LogCategory
from .parser import LogConfigParser



# We need to know where we are first.
# DO not use the way borrowed from python's logging.
# It cannot be used in zip library!!!
_THIS_FILE = inspect.currentframe().f_code.co_filename
_THIS_FILE = os.path.normcase(os.path.abspath(os.path.normpath(_THIS_FILE)))

# For convenient.
CWD = os.path.normcase(os.path.abspath(os.getcwd()))
PATHS = [os.path.normcase(os.path.abspath(i)) for i in sys.path]

# Python documentation says:
#   As initialized upon program startup, the first item of this list, path[0],
#   is the directory containing the script that was used to invoke the Python
#   interpreter. If the script directory is not available (e.g. if the
#   interpreter is invoked interactively or if the script is read from standard
#   input), path[0] is the empty string, which directs Python to search modules
#   in the current directory first.
PATHS.append(CWD)  # CWD may be the sub-directory of one other path.
if PATHS[0] == CWD:
    PATHS.pop(0)
else:
    # The directory of running script may be the sub-directory of
    # one other path, including CWD.
    PATHS.append(PATHS.pop(0))

# Final result for cutting common prefix.
PATHS = [(i, len(i)) for i in PATHS]



def _find_caller():
    """
    Find the stack frame of the caller so that we can note
    the source file name and line number.
    """
    f = sys._getframe().f_back
    filename, lineno = 'unknown_file', 'unknown_lineno'

    while hasattr(f, 'f_code'):
        co = f.f_code
        filename = os.path.normcase(os.path.abspath(co.co_filename))

        if filename == _THIS_FILE:
            f = f.f_back
            continue

        for path, len_path in PATHS:
            if filename.startswith(path):
                filename = filename[len_path + 1:]
                break

        lineno = f.f_lineno
        break

    return filename, lineno



def _decode_msg(*args):
    """
    Decode sequence of messages.
    """
    msgs = []

    for arg in args:
        try:
            if isinstance(arg, unicode):
                msgs.append( arg.encode('utf-8'))
        except:
            pass
        finally:
            if not isinstance(arg, str):
                msgs.append(str(arg))
            else:
                msgs.append(arg)

    return ' '.join(msgs)



def _log_msg(category, continuation, *args, **kwargs):
    """
    Function of supporting other public interfaces.
    """
    filename, lineno = _find_caller()
    LogStream.lock_out_other_threads(True)

    if not LogStream.suppressed(category, filename, lineno, continuation):
        msg = _decode_msg(*args)
        exc_info = kwargs.pop('exc_info', None)

        if exc_info:
            if not msg:
               msg = 'Exception occurs.'
            if not msg.endswith(os.linesep):
                msg += os.linesep

            sio = StringIO()
            traceback.print_exception(exc_info[0], exc_info[1],
                                      exc_info[2], file=sio)
            msg += sio.getvalue().strip()
            sio.close()

        LogStream.sink_msg(msg)

    LogStream.lock_out_other_threads(False)



def use(*args):
    """
    Log given message in USE category.
    """
    _log_msg(LogCategory.USE, False, *args)



def diag(*args):
    """
    Log given message in DIAG category.
    """
    _log_msg(LogCategory.DIAG, False, *args)



def event(*args):
    """
    Log given message in EVENT category.
    """
    _log_msg(LogCategory.EVENT, False, *args)



def problem(*args):
    """
    Log given message in PROBLEM category.
    """
    _log_msg(LogCategory.PROBLEM, False, *args)



def warning(*args):
    """
    Log given message in WARNING category.
    """
    _log_msg(LogCategory.WARNING, False, *args)



def bug(*args):
    """
    Log given message in BUG category.
    """
    _log_msg(LogCategory.BUG, False, *args)



def debug(*args):
    """
    Log given message in DEBUG category.
    """
    _log_msg(LogCategory.DEBUG, False, *args)



def verbose(*args):
    """
    Log given message in VERBOSE category.
    """
    _log_msg(LogCategory.VERBOSE, False, *args)



def exception(*args):
    """
    Log given message with exception information in PROBLEM category.
    """
    _log_msg(LogCategory.PROBLEM, False, *args, exc_info=sys.exc_info())



def _(*args):
    """
    Log given message without prefix in DIAG category.

    This works for process log only.
    """
    _log_msg(LogCategory.DIAG, False, *args)



def set_auto_break_at_midnight(enabled=True):
    """
    Set automation mode of breaking log file at midnight.
    """
    LogStream.lock_out_other_threads(True)
    LogStream.set_auto_break_at_midnight(enabled)
    LogStream.lock_out_other_threads(False)



def break_log_file():
    """
    Manually break log file.
    """
    LogStream.lock_out_other_threads(True)
    LogStream.break_log_file()
    LogStream.lock_out_other_threads(False)



def set_log_config(config_path):
    """
    Set where the log configuration file is.
    """
    if not os.path.isabs(config_path):
        config_path = os.path.abspath(config_path)

    LogStream.lock_out_other_threads(True)
    LogConfigParser.LOG_CONFIG = config_path
    LogStream.lock_out_other_threads(False)



def set_log_dir(log_dir):
    """
    Set the directory path for the process log file.
    """
    if not os.path.isabs(log_dir):
        log_dir = os.path.abspath(log_dir)

    LogStream.lock_out_other_threads(True)
    LogStream.log_dir = log_dir
    LogStream.lock_out_other_threads(False)



def set_log_name(log_name):
    """
    Set the process log file name.
    """
    LogStream.lock_out_other_threads(True)
    LogStream.log_name = log_name
    LogStream.lock_out_other_threads(False)



def set_log_backup_count(value):
    """
    Set process logs' backup count.
    """
    LogStream.lock_out_other_threads(True)
    LogStream.log_backup_count = int(value)
    LogStream.lock_out_other_threads(False)



def set_collective_dir(collective_dir):
    """
    Set the directory path for the collective log file.
    """
    if not os.path.isabs(collective_dir):
        collective_dir = os.path.abspath(collective_dir)

    LogStream.lock_out_other_threads(True)
    LogStream.collective_dir = collective_dir
    LogStream.lock_out_other_threads(False)



def set_collective_name(collective_name):
    """
    Set the collective log file name.
    """
    LogStream.lock_out_other_threads(True)
    LogStream.collective_name = collective_name
    LogStream.lock_out_other_threads(False)



def set_collective_backup_count(value):
    """
    Set collective logs' backup count.
    """
    LogStream.lock_out_other_threads(True)
    LogStream.collective_backup_count = int(value)
    LogStream.lock_out_other_threads(False)
