#!/home/cb/.pyenv/versions/dj18/bin/python
#  -*- coding: utf-8 -*-
from __future__ import (absolute_import)
import os
import sys
import time


def dump_sys_path():
    with open("/tmp/aaa", "w") as fp:
        fp.writelines("%s\n" % sys.version)
        for aa in sys.path:
            fp.writelines("%s\n" % aa)


from module import log

program_path = os.path.abspath(__file__)
program_dir = os.path.dirname(program_path)
log.set_log_config(
    os.path.join(program_dir, "__dev_tests", "log.file_drive_service.conf"))
log.set_collective_dir(program_dir)
log.set_collective_name("zzz")

from .filedrive import FileDrive
from .timedrive import TimeDrive
from .service import LinuxService

if __name__ == "__main__":
    program_name = os.path.basename(program_path)
    pid_file = os.path.join(program_dir, '.%s.pid' % program_name)

    if len(sys.argv) > 1:
        if sys.argv[1] == 'filedrive':
            config_file = os.path.join(
                program_dir, "__dev_tests", "file_drive_service.conf")

            ingest = FileDrive(config_file)
            ingest_service = LinuxService(ingest, program_path, pid_file)
        elif sys.argv[1] == 'timedrive':
            config_file = os.path.join(
                program_dir, "__dev_tests", "timedrive_service.conf")

            timedrive = TimeDrive(config_file)
            timedrive_service = LinuxService(timedrive, program_path, pid_file)
