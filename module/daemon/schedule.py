# -*- coding: utf-8 -*-
from __future__ import (absolute_import)
from .aps_logging import *

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.memory import MemoryJobStore

from .job import JobManager

from module import log

JOBSTORES = {
    'default': MemoryJobStore()
}

EXECUTORS = {
    'default': {'type': 'threadpool', 'max_workers': 5}
}

JOB_DEFAULTS = {
    'coalesce': False,
    'max_instances': 5
}

SCHEDULER = BackgroundScheduler()


class ScheduleManager(object):
    """
        To wrap APScheduler as a Module
    """

    def __init__(self, config):
        self.scheduler = SCHEDULER
        self.config = config
        try:
            self.scheduler.configure(
                jobstores=JOBSTORES,
                executors=EXECUTORS,
                job_defaults=JOB_DEFAULTS,
                timezone='Asia/Taipei'
            )
            self.jm = JobManager(self.scheduler, self.config)
        except Exception:
            log.exception('Scheduler Configure Failed!')

    def startup(self):
        try:
            self.add_jobs()
            self.scheduler.start()
        except Exception:
            log.exception('Scheduler Startup Failed!')

    def shutdown(self):
        try:
            self.scheduler.shutdown()
        except Exception:
            log.exception('Scheduler Shutdown Failed!')

    @property
    def is_running(self):
        return self.scheduler.running

    def status(self):
        return self.scheduler.state

    def add_jobs(self):
        self.jm.add_jobs()

    def remove_jobs(self):
        self.jm.remove_jobs()

    def check_jobs(self):
        self.jm.check_jobs()

    def list_job(self):
        pass
