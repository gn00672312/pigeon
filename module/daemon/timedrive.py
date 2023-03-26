# -*- coding: utf-8 -*-
from __future__ import (absolute_import)
import os
import time
from datetime import datetime, tzinfo

from . import util
from .schedule import ScheduleManager
from .process import Process

DEFAULT_ARGS = {
    'DIR_SCRIPT': {
        'val': '',
        'type': str,
        'mandatory': False,
        'is_path': True
    },
    'JOB': {
        'val': [],
        'type': list,
        'mandatory': False
    },
    'SECS_TIMEOUT_FOR_ACTION':  {
        'val': 0,
        'type': int,
        'mandatory': True,
        'min_value': 0,
    },
}


DEFAULT_JOB = {
    'action': {
        'val': {},
        'type': dict,
        'mandatory': True
    },
    'cron': {
        'val': {},
        'type': dict,
        'mandatory': False,
    },
    'interval': {
        'val': {},
        'type': dict,
        'mandatory': False,
    }
}

DEFAULT_ACTION = {
    'executable': {
        'val': 'python',
        'type': str,
        'mandatory': False
    },
    'script': {
        'val': '',
        'type': (list, tuple, str),
        'mandatory': False
    },
    'cwd': {
        'val': util.CWD,
        'type': str,
        'mandatory': False
    },
    'argument': {
        'val': '',
        'type': str,
        'mandatory': False
    },
    'timeout':  {
        'val': -99,
        'type': int,
        'mandatory': False,
        'min_value': 0,
    }
}

DEFAULT_CRON = {
    'year': {
        'val': None,  # (int|str) – 4-digit year
        'type': (int, str),
        'mandatory': False
    },
    'month': {
        'val': None,  # (int|str) – month (1-12)
        'type': (int, str),
        'mandatory': False
    },
    'day': {
        'val': None,  # (int|str) – day of the (1-31)
        'type': (int, str),
        'mandatory': False
    },
    'week': {
        'val': None,  # (int|str) – ISO week (1-53)
        'type': (int, str),
        'mandatory': False
    },
    'day_of_week': {
        'val': None,  # (int|str) – number or name of weekday (0-6 or mon,tue,wed,thu,fri,sat,sun)
        'type': (int, str),
        'mandatory': False
    },
    'hour': {
        'val': None,  # (int|str) – hour (0-23)
        'type': (int, str),
        'mandatory': False
    },
    'minute': {
        'val': None,  # (int|str) – minute (0-59)
        'type': (int, str),
        'mandatory': False
    },
    'second': {
        'val': None,  # (int|str) – second (0-59)
        'type': (int, str),
        'mandatory': False
    },
    'start_date': {
        'val': None,  # (datetime|str) – earliest possible date/time to trigger on (inclusive)
        'type': (datetime, str),
        'mandatory': False
    },
    'end_date': {
        'val': None,  # (datetime|str) – latest possible date/time to trigger on (inclusive)
        'type': (datetime, str),
        'mandatory': False
    },
    'timezone': {
        'val': None,  # (datetime.tzinfo|str) – time zone to use for the date/time calculations (defaults to scheduler timezone)
        'type': (tzinfo, str),
        'mandatory': False
    },
    'jitter': {
        'val': None,  # (int|None) – advance or delay the job execution by jitter seconds at most.
        'type': (int),
        'mandatory': False
    }
}


DEFAULT_INTERVAL = {
    'weeks': {
        'val': 0,  # (int) – number of weeks to wait
        'type': int,
        'mandatory': False
    },
    'days': {
        'val': 0,  # (int) – number of days to wait
        'type': int,
        'mandatory': False
    },
    'hours': {
        'val': 0,  # (int) – number of hours to wait
        'type': int,
        'mandatory': False
    },
    'minutes': {
        'val': 0,  # (int) – number of minutes to wait
        'type': int,
        'mandatory': False
    },
    'seconds': {
        'val': 0,  # (int) – number of seconds to wait
        'type': int,
        'mandatory': False
    },
    'start_date': {
        'val': None,  # (datetime|str) – starting point for the interval calculation
        'type': (datetime, str),
        'mandatory': False
    },
    'end_date': {
        'val': None,  # (datetime|str) – latest possible date/time to trigger on
        'type': (datetime, str),
        'mandatory': False
    },
    'timezone': {
        'val': None,  # (datetime.tzinfo|str) – time zone to use for the date/time calculations
        'type': (tzinfo, str),
        'mandatory': False
    },
    'jitter': {
        'val': None,  # (int|None) – advance or delay the job execution by jitter seconds at most.
        'type': (int),
        'mandatory': False
    }
}


class TimeDrive(Process):

    def __init__(self, config_file=None):
        super(TimeDrive, self).__init__(config_file)
        self.config = self.import_config(config_file)
        self.scheduler = ScheduleManager(self.config)

    def startup(self):
        self.scheduler_startup()

        while not self.TERMINATING:
            self.check_jobs()
            time.sleep(0.4)

    def scheduler_startup(self):
        self.scheduler.startup()

    def check_jobs(self):
        self.scheduler.check_jobs()

    @classmethod
    def import_config(cls, config_file):
        _config = util.read_conf(config_file)
        config = util.check_and_set_default_config(_config, DEFAULT_ARGS)

        for job in config.get('JOB', []):
            _job = util.check_and_set_default_config(job, DEFAULT_JOB)
            job = _job

            if ((job['cron'] and job['interval']) or
                    (not job['cron'] and not job['interval'])):
                lvl = ['JOB']
                msg = 'either "cron" or "interval" must be set.'
                raise util.ConfigError(lvl, msg)

            # for action in job['action']:
            # check filedrive task action arguments type and assign to config
            job_action = job['action']
            action_config = util.check_and_set_default_config(
                job_action, DEFAULT_ACTION)

            executable = job_action.get('executable', False)
            script = job_action.get('script', False)

            # special check config
            # executable must be either absolute or basename.
            if executable:
                if (os.path.basename(executable) != executable and
                        not os.path.isabs(executable)):
                    lvl = ['JOB', 'action', 'executable']
                    msg = 'must be either absolute or only basename.'
                    raise util.ConfigError(lvl, msg)

            # Either executable or script must be provided.
            if not executable and not script:
                lvl = ['JOB', 'action']
                msg = 'either "executable" or "script" must be set.'
                raise util.ConfigError(lvl, msg)

            if action_config['timeout'] == -99:
                action_config['timeout'] = config["SECS_TIMEOUT_FOR_ACTION"]

            job_action.update(action_config)

            if job['cron']:
                job_cron = job['cron']
                cron_config = util.check_and_set_default_config(
                    job_cron, DEFAULT_CRON)

                job_cron.update(cron_config)

            if job['interval']:
                job_interval = job['interval']
                interval_config = util.check_and_set_default_config(
                    job_interval, DEFAULT_INTERVAL)

                job_interval.update(interval_config)

        return config


if __name__ == "__main__":
    time_drive = TimeDrive('timedrive.conf')
    time_drive.startup()
