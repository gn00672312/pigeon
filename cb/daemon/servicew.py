# -*- coding: utf-8 -*-

import win32serviceutil
import win32service
import win32event
import servicemanager
import socket

from module import log
__author__ = 'CloudyBay'


class WindowService(win32serviceutil.ServiceFramework):
    """
    for developer
    overwrite
        _svc_name_
        _svc_display_name_
        main()

    set the main process as self.process and implement method stop(), see
    SvcStop()

    """

    _svc_name_ = "TestService"
    _svc_display_name_ = "Test Service"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)
        self.stop_requested = False

    def SvcStop(self):
        log.event("stop service")
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.stop_requested = True
        try:
            self.process.stop()
        except:
            raise

    def SvcDoRun(self):
        log.event("start service ")
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_, ''))
        self.main()

    def main(self):
        while not self.stop_requested:
            pass


'''
import time
import datetime

from servicew import *


class MyProjectService(WindowService):
    _svc_name_ = "MyProjectService"
    _svc_display_name_ = "MyProject Service"

    def main(self):
        with open("E:\\out.txt", "w") as fp:
            while not self.stop_requested:
                now = datetime.datetime.now()
                if now.second % 10 == 0:
                    fp.writelines("Hello! World! %s\n" % now)
                time.sleep(1)


if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(WindowService)

'''
