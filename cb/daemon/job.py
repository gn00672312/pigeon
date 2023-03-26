# -*- coding: utf-8 -*-
from __future__ import (absolute_import)
import os
import uuid
import time

from collections import deque
from apscheduler.util import (undefined)

from . import util
from .shell import Shell, DEFAULT_TIMEOUT
from module import log


class JobManager(object):
    def __init__(self, schduler, config):
        self.scheduler = schduler
        self.config = config
        self.jobs = deque()

    def add_jobs(self):
        try:
            for _job_config in self.config['JOB']:
                _job = Job(self.scheduler, _job_config, self.config['DIR_SCRIPT'])
                _job.add()
                self.jobs.append(_job)
        except Exception:
            log.exception()

    def remove_jobs(self):
        try:
            jobs_len = len(self.jobs)
            for i in range(jobs_len):
                _job = self.jobs.popleft()
                _job.remove()
        except Exception:
            log.exception()

    def check_jobs(self):
        try:
            jobs_len = len(self.jobs)
            for i in range(jobs_len):
                job = self.jobs.popleft()
                to_remove = job.check_job()
                if to_remove:
                    job.remove()
                else:
                    self.jobs.append(job)
        except:
            log.exception()


class Job(object):
    trigger = None
    args = None
    kwargs = None
    id = None
    name = None
    misfire_grace_time = undefined
    coalesce = undefined
    max_instances = undefined
    next_run_time = undefined
    jobstore = 'default'
    executor = 'default'
    replace_existing = True
    runner_q = deque()
    count = 0
    max_runners = -1

    def __init__(self, scheduler, job_config, dir_script):
        self.scheduler = scheduler
        self.job_config = job_config

        if 'cron' in job_config:
            self.trigger = 'cron'
        elif 'interval' in job_config:
            self.trigger = 'interval'

        self.trigger_args = job_config[self.trigger]
        self.id = str(uuid.uuid1())

        self.__python = util.which('python')
        self.__dir_script = dir_script

        self._make_runner()

    def check_job(self):
        runners_len = len(self.runner_q)
        for i in range(runners_len):
            runner = self.runner_q.popleft()
            runner.log(self.name)
            if runner.returncode is None:
                self.runner_q.append(runner)

        return self.max_runners > 0 and self.count >= self.max_runners

    def _make_runner(self):
        env = os.environ.copy()
        kwargs = dict(env=env)

        action = self.job_config.get('action', {})

        script_path = action.get('script', '')
        if script_path:
            # Todo: how to get dir_script
            script_path = util.force_abs(self.__dir_script, script_path)

        script_name = os.path.basename(script_path)
        if script_name.endswith(('.py', '.pyc', '.pyo')):
            # For Python scripts, reset all log files name.
            script_name = os.path.splitext(script_name)[0]
            env['LOG_NAME'] = env['COLLECTIVE_NAME'] = script_name

        executable = action.get('executable')
        if executable and not os.path.isabs(executable):
            executable = util.which(executable)

        args = [executable or self.__python]
        if script_path:
            args.append(script_path)

        argument = action.get('argument', None)
        if argument:
            args.append(argument)

        cwd = action.get('cwd')
        if cwd:
            kwargs['cwd'] = cwd
        else:
            kwargs['cwd'] = util.CWD

        self.args = args
        self.kwargs = kwargs
        self.name = " ".join(str(i) for i in self.args)

    def runner_func(self):
        runner = Runner(self.job_config['action']['timeout'])
        self.runner_q.append(runner)
        runner.run(*self.args, **self.kwargs)
        self.count += 1
        log.event("ACTION executed",
                  ', PID=', runner.pid,
                  ", cmd={", runner.cmd, "}")

    def add(self):
        try:
            self.count = 0
            self.scheduler.add_job(
                func=self.runner_func,
                # args=self.args,
                # kwargs=self.kwargs,
                name=self.name,
                trigger=self.trigger,
                id=self.id,
                replace_existing=self.replace_existing,
                **self.job_config.get(self.trigger, {})
            )
        except Exception:
            log.exception()

    def remove(self):
        try:
            for runner in self.runner_q:
                runner.kill()
            self.runner_q = deque()
            self.scheduler.remove_job(self.id)

        except:
            log.exception()


class Runner(Shell):
    logged = False

    def __init__(self, timeout=DEFAULT_TIMEOUT):
        super(Runner, self).__init__(timeout)

    def log(self, name):
        # done() will kill runner with checking timeout, make sure to call it.
        _done = self.done()
        if (_done and
                self.stderr and
                not self.is_success and
                not self.logged):

            log.diag('Job \"{0}\" failed, \npid: {1} \nstdout: {2} \nstderr: {3}\nreturn code:{4}'.format(
                name, self.pid, self.stdout, self.stderr, self.returncode))
            self.logged = True

    @property
    def is_success(self):
        if self.returncode == 0:
            return True
        return False