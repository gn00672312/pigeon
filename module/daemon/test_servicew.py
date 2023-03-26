# -*- coding: utf-8 -*-

import os
import time
import datetime

from module import log

program_path = os.path.abspath(__file__)
program_dir = os.path.dirname(program_path)
log.set_log_config(
    os.path.join(program_dir, "__dev_tests", "log.file_drive_service.conf"))
log.set_collective_dir(program_dir)
log.set_collective_name("cb_servicew")

from .servicew import *

from .filedrive import FileDrive


class FileDriveService(WindowService):
    _svc_name_ = "FileDriveService"
    _svc_display_name_ = "FileDrive Service"

    def main(self):
        program_name = os.path.basename(program_path)
        config_file = os.path.join(
            program_dir, "__dev_tests", "file_drive_servicew.conf")
        # config_file = None
        self.process = FileDrive(config_file)
        self.process.startup()


if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(FileDriveService)
