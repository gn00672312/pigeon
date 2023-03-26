# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import

"""
This file is designed for programmer to install / uninstall their programs
to be / from Linux services with ease. To use this utility, you should have
already basic ideas regarding Linux system service.
"""
import os
import sys
import pwd
import time
import stat
import fcntl
import errno
import signal
# import exceptions

from .shell import Shell

from module import log

SERVICE_SCRIPT = """\
#!/bin/bash
#
# chkconfig: %(run_levels)s %(priority_start)s %(priority_stop)s
#
# description: Startup and shutdown script for %(service_name)s.
###############################################################################
. %(dir_init_scripts)s/functions



RVAL=0
RUNNER="$(id -u -n)"
OWNER="%(service_owner)s"
SERVICE="%(service_name)s"
PYTHON="%(which_python)s"
COMMAND="%(command_script)s"
PID_FILE="%(pid_file)s"
ARG_START="%(params_start)s"
ARG_STOP="%(params_stop)s"



#------------------------------------------------------------------------------
# Starts up %(service_name)s process.
#------------------------------------------------------------------------------
start()
{
    echo -n $"Starting ${SERVICE}: "

    if [ "${RUNNER}" = "${OWNER}" ]; then
        ${PYTHON} ${COMMAND} ${ARG_START}
        RVAL="$?"
    elif [ "${RUNNER}" = "root" ]; then
        su - ${OWNER} -c "${PYTHON} ${COMMAND} ${ARG_START}"
        RVAL="$?"
    else
        echo -n $"user not authorized: ${RUNNER}"
        RVAL=1
    fi

    [ "${RVAL}" -eq 0 ] && success || failure
    echo
    return ${RVAL}
}



#------------------------------------------------------------------------------
# Shutdowns down %(service_name)s process.
#------------------------------------------------------------------------------
stop()
{
    echo -n $"Stopping ${SERVICE}: "

    if [ "${RUNNER}" = "${OWNER}" ]; then
        ${PYTHON} ${COMMAND} ${ARG_STOP}
        RVAL="$?"
    elif [ "${RUNNER}" = "root" ]; then
        su - ${OWNER} -c "${PYTHON} ${COMMAND} ${ARG_STOP}"
        RVAL="$?"
    else
        echo -n $"user not authorized: ${RUNNER}"
        RVAL=1
    fi

    [ "${RVAL}" -eq 0 ] && success || failure
    echo
    return ${RVAL}
}



#------------------------------------------------------------------------------
# Action based on argument.
#------------------------------------------------------------------------------
case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    status)
        status -p ${PID_FILE} ${PYTHON} ${COMMAND}
        ;;
    restart)
        stop
        start
        ;;
    *)
        echo $"Usage: ${SERVICE} {start|stop|status|restart}"
        exit 1
esac

exit $?

"""


class Service(object):
    """
    A wrapper class to install/uninstall a program as/from the service.
    """
    CHKCONFIG = '/sbin/chkconfig'
    DIR_INIT_SCRIPTS = '/etc/rc.d/init.d'

    PRIORITY_START = '99'
    PRIORITY_STOP = '01'
    RUN_LEVELS = '345'
    MODE = 0o755

    def __init__(self, program_path, service_name=None, service_owner=None,
                 params_start=None, params_stop=None, pid_file=None):
        """
        Initialize a new Service instance.
          - program_path
            is the real path to be executed.
          - service_name
            is the name will be installed to be the system service.
            The basename of program_path will be used if not specified.
          - service_owner
            is the process owner while this service is running.
            If not specified, root will be the default owner.
          - params_start
            is the parameters, in string format if specified, to be used
            to start the service up.
          - params_stop
            is the parameters, in string format if specified, to be used
            to shut the service down.
          - pid_file
            is the file path to write service PID to. If not specified,
            .service_name.pid will be used under current working directory.
        """
        self.__command_script = ss = os.path.abspath(program_path)
        self.__service_name = service_name
        self.__service_owner = service_owner or 'root'
        self.__params_start = params_start or ''
        self.__params_stop = params_stop or ''
        self.__pid_file = pid_file

        if self.__service_name is None:
            self.__service_name = os.path.splitext(os.path.basename(ss))[0]

        if self.__pid_file is None:
            dir_script = os.path.dirname(ss)
            pid_filename = '.%s.pid' % self.__service_name
            self.__pid_file = os.path.join(dir_script, pid_filename)

        self.__service_script = os.path.join(self.DIR_INIT_SCRIPTS,
                                             self.__service_name)

        self.__sh = Shell()
        self.__out = lambda msg: sys.stdout.write('%s\n' % msg)
        self.__error = lambda msg: sys.stderr.write('Error: %s\n' % msg)
        self.__warn = lambda msg: sys.stderr.write('Warning: %s\n' % msg)
        self.__which_python = sys.executable

    def install_service(self, run_levels=None, priority_start=None,
                        priority_stop=None):
        """
        Install this process to be a Linux service. If parameters are specified,
        they must be strings, or unexpect result may be raised. The default
        run_levels is '345', the default priority_start is '99', while the
        default priority_stop is '01'.
        """
        if os.getuid() != 0:
            self.__error('install services need root permission.')
            return False

        if run_levels is None:
            run_levels = self.RUN_LEVELS
        if priority_start is None:
            priority_start = self.PRIORITY_START
        if priority_stop is None:
            priority_stop = self.PRIORITY_STOP

        kws = dict(dir_init_scripts=self.DIR_INIT_SCRIPTS,
                   service_name=self.__service_name,
                   service_owner=self.__service_owner,
                   run_levels=run_levels,
                   priority_start=priority_start,
                   priority_stop=priority_stop,
                   pid_file=self.__pid_file,
                   which_python=self.__which_python,
                   command_script=self.__command_script,
                   params_start=self.__params_start,
                   params_stop=self.__params_stop)

        try:
            with open(self.__service_script, 'w') as script:
                script.write(SERVICE_SCRIPT % kws)
        except Exception as e:
            self.__error('failed to add service: %s' % e)
            return False

        if stat.S_IMODE(os.stat(self.__service_script).st_mode) != self.MODE:
            try:
                os.chmod(self.__service_script, self.MODE)
            except:
                self.__warn('cannot set proper permission to service script.')

        self.__sh.run(self.CHKCONFIG, 'add', self.__service_name).wait()
        if self.__sh.returncode != 0:
            self.__error('failed to add service: %s' % self.__sh.stderr)
            return False

        self.__out('Service "%s" installed.' % self.__service_name)
        return True

    def uninstall_service(self):
        """
        Uninstall this process from Linux service.
        """
        if os.getuid() != 0:
            self.__error('uninstall services need root permission.')
            return False

        self.__sh.run(self.CHKCONFIG, 'del', self.__service_name).wait()
        if self.__sh.returncode != 0:
            self.__error('failed to remove service: %s' % self.__sh.stderr)
            return False

        try:
            os.remove(self.__service_script)
        except:
            self.__warn('failed to remove file: %s' % self.__service_script)

        self.__out('Service "%s" uninstalled.' % self.__service_name)
        return True


class LinuxService(object):
    TERMINATING = False

    def __init__(
            self, service_process, program_path=__file__, pid_file=None):
        self.process = service_process

        self.program_path = program_path
        if not os.path.isfile(self.program_path):
            raise IOError
        self.program_name = os.path.basename(program_path)
        self.program_dir = os.path.dirname(program_path)

        self.pid_file = pid_file
        if pid_file is None:
            self.pid_file = os.path.join(
                self.program_dir, "." + self.program_name)
        try:
            # self.pid_file = self.process.pid_file
            self.process.set_pid_file(self.pid_file)
        except:
            log.exception()
            raise

        '''
        self.default_config_dir = os.path.join(
            os.path.dirname(self.program_dir), "conf")
        self.default_config_name = '%s.conf' % self.program_name
        self.default_config_path = os.path.join(
            self.default_config_dir, self.default_config_name)

        if config_dir is None:
            config_dir = self.default_config_dir
        if config_name is None:
            config_name = self.default_config_name
        self.config_path = os.path.join(config_dir, config_name)
        '''

        self.file_owner = pwd.getpwuid(os.stat(program_path).st_uid).pw_name
        self.__lock_file = None

        self.options = self.decode_arguments()
        self.run()

    def usage(self):
        usage = '''\
    USAGE
            {program_name} [OPTIONS]...

    DESCRIPTION
            This utility lets users to run and/or control the execution program.

    CONFIGURATION
            The default configuration file is named '{config_name}'
            and is populated under {config_dir} directory. You can have
            your own by using corresponding option.

    OPTIONS
            -d, --daemonize
                    Run process as daemon mode instead of terminal mode.
                    Incompatible with -s option.

            -s, --shutdown
                    Shutdown process. Incompatible with -d option.

            -i, --install-service
                    Install this process as a system service. Incompatible
                    with -u option.

            -u, --uninstall-service
                    Un-install this process from system services. Incompatible
                    with -i option.

            -f FILE, --config-file=FILE
                    Use a custom configuration file instead of default one.
                    If the FILE is not an absolutely path, it will be searched
                    from current working directory.

            -h, --help
                    Show this message you are reading.
    '''.format(program_name=self.program_name,
               config_name=self.process.default_config_name,
               config_dir=self.process.default_config_dir)
        print(usage)

    def decode_arguments(self):
        import getopt
        try:
            long = ['daemonize', 'shutdown', 'install-service',
                    'uninstall-service', 'config-file=', 'help']
            opts, args = getopt.getopt(sys.argv[1:], 'dsiuf:h', long)
        except:
            log.exception('Decode argument error.')
            sys.exit(1)

        class Option(object):
            daemonize = shutdown \
                = install_service \
                = uninstall_service \
                = False
            config_file = None

        option = Option()
        for opt, arg in opts:
            if opt in ('-d', '--daemonize'):
                option.daemonize = True
            elif opt in ('-s', '--shutdown'):
                option.shutdown = True
            elif opt in ('-i', '--install-service'):
                option.install_service = True
            elif opt in ('-u', '--uninstall-service'):
                option.uninstall_service = True
            elif opt in ('-f', '--config-file'):
                if arg:
                    option.config_file = os.path.abspath(arg)
                else:
                    log.problem('Invalid configuration file name provided!')
                    sys.exit(1)
            elif opt in ('-h', '--help'):
                if sys.stdout.isatty():
                    self.usage()
                sys.exit(0)

        if option.install_service and option.uninstall_service:
            log.problem('Error usage: -i and -u show together.')
            sys.exit(1)
        if option.daemonize and option.shutdown:
            log.problem('Error usage: -d and -s show together.')
            sys.exit(1)
        return option

    def run(self):
        service = Service(self.program_path, service_owner=self.file_owner,
                          params_start='-d', params_stop='-s',
                          pid_file=self.pid_file)
        if self.options.install_service:
            service.install_service()
            sys.exit(0)
        elif self.options.uninstall_service:
            service.uninstall_service()
            sys.exit(0)

        if self.options.shutdown:
            sys.exit(0 if self.process.shutdown_for_linux_service() else 1)

        try:
            if self.options.daemonize:
                self.process.daemonize()
                os.chdir(self.program_dir)
            else:
                os.umask(0)

            # Remember this method call must be made after daemonize().
            if not self.process.lock_for_linux_service():
                log.problem('Another instance is running.')
                sys.exit(1)

            self.process.write_pid_for_linux_service()
            self.process.install_signal_handlers()
            self.process.set_config(self.options.config_file)
            self.process.startup()
        except Exception:
            log.exception()
            # log.exception(self.program_name, ' error.')
        finally:
            self.process.unlock_for_linux_service()
