from __future__ import print_function
import os
import re
import sys



# Check OS platform.
OS_POSIX = OS_WIN = False

if sys.platform.startswith('win'):
    OS_WIN = True
elif sys.platform.startswith('linux'):
    OS_POSIX = True
elif sys.platform.startswith('darwin'):
    OS_POSIX = True
else:
    raise NotImplementedError('log package not support for %s' % sys.platform)



if OS_WIN:
    try:
        import win32api
        import win32con
        import win32file
        import pywintypes
    except ImportError:
        raise EnvironmentError('pywin32 extension is mandatory to log package')


    LOCK_EX = win32con.LOCKFILE_EXCLUSIVE_LOCK
    OVERLAPPED = pywintypes.OVERLAPPED()


    def _acquire(fd):
        """
        Acquire lock of the given file descriptor.
        """
        try:
            handle = win32file._get_osfhandle(fd)
            win32file.LockFileEx(handle, LOCK_EX, 0, -0x10000, OVERLAPPED)
        except Exception as e:
            print (e, file=sys.__stderr__)
            return False
        return True


    def _release(fd):
        """
        Release acquired lock of the given file descriptor.
        """
        try:
            handle = win32file._get_osfhandle(fd)
            win32file.UnlockFileEx(handle, 0, -0x10000, OVERLAPPED)
        except Exception:
            return False
        return True


    def _get_arg0():
        """
        Getting argument 0, the executable itself.

        If it's the python interpreter, using the running script name instead.
        """
        try:
            arg0 = win32api.GetModuleFileName(0)
        except Exception:
            # Use script's name as process name if we can't get in normal way.
            arg0 = sys.argv[0]

        # Case of using python interpreter to run script.
        if os.path.basename(arg0) in ('python.exe', 'pythonw.exe'):
            args = sys.argv[0]

        return arg0



if OS_POSIX:
    import fcntl
    import errno


    LOCK_EX = fcntl.LOCK_EX


    def _acquire(fd):
        """
        Acquire lock of the given file descriptor.
        """
        while True:
            try:
                fcntl.flock(fd, LOCK_EX)
            except OSError as err:
                no = err[0]
                msg = err[1]
                if no == errno.EINTR:
                    continue
                else:
                    print (msg, file=sys.__stderr__)
                    return False
            return True


    def _release(fd):
        """
        Release acquired lock of the given file descriptor.
        """
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        except Exception:
            return False
        return True


    def _get_arg0():
        """
        Getting argument 0, the executable itself.

        If it's the python interpreter, using the running script name instead.
        """
        arg0 = ''
        try:
            f = open('/proc/self/cmdline')
            while True:
                c = f.read(1)
                if c == '\0':
                    break
                arg0 += c
        except Exception:
            # Either can't get in normal way or we are on MAC OS.
            # Use script as process name till I can figure out
            # how to get arg0 under MAC.
            arg0 = sys.argv[0]

        # Strip spaces.
        arg0 = arg0.strip()

        # Check if we are using interpreter to run script.
        name = os.path.basename(arg0)
        if name == 'python' or re.match('python\d+(\.?\d+)+', name):
            arg0 = sys.argv[0]

        return arg0



class LogFileLock(object):
    """
    Class to implement file locking mechanism so that the goal of
    process-safe can be achieved, easily.
    """
    def __init__(self, file):
        self._file = file
        self._locked = True
        self._acquire()


    def __del__(self):
        self._release()


    def got_lock(self):
        return self._locked


    def _acquire(self):
        self._locked = _acquire(self._file.fileno())


    def _release(self):
        _release(self._file.fileno())
        self._locked = False



def get_process_name(use_full_path=False):
    """
    Getting the current process's name.

    If 'use_full_path' is True, return the full path name.
    If 'use_full_path' is False, the default, just return its basename.
    """
    if not hasattr(get_process_name, 'full_name'):
        arg0 = _get_arg0()

        # We don't want file extension if this process is
        # the python interpreter itself.
        if arg0.endswith('.py'):
            arg0 = arg0[:-3]
        elif arg0.endswith('.pyw'):
            arg0 = arg0[:-4]

        # Full path wanted.
        if not os.path.isabs(arg0):
            arg0 = os.path.join(os.getcwd(), arg0)

        # Make it.
        get_process_name.full_name = os.path.normpath(arg0)

    if not hasattr(get_process_name, 'leaf_name'):
        full_name = get_process_name.full_name
        get_process_name.leaf_name = os.path.basename(full_name)

    return get_process_name.full_name if use_full_path else\
           get_process_name.leaf_name



def format_datetime(datetime):
    rv = datetime.strftime('%Y-%m-%d %H:%M:%S')
    rv += ',%03i' % (datetime.microsecond / 1000)
    return rv
