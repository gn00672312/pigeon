# -*- coding: utf-8 -*-
from __future__ import (absolute_import)

import re
import time
import os
from collections import OrderedDict

from .shell import Shell
from . import util
from module import log


class QueueManager(object):
    (SUCCESS,
     FILE_NOT_AVALIABLE,
     ALREADY_IN_QUEUE
     ) = range(3)

    def __init__(self, config):
        self.running = {}
        self.config = config

        queue_dict = {}
        for queue_id, queue_config in config["QUEUE"].items():
            queue_dict[queue_id] = Queue(
                queue_id, queue_config, config["DIR_SCRIPT"])

        self.queue_ordered_dict = OrderedDict(
            sorted(queue_dict.items(), key=lambda t: t[1].priority))

    @staticmethod
    def mtime_age(path):
        try:
            return time.time() - os.path.getmtime(path)
        except:
            # No age no matter why we can't get mtime.
            return 0

    @staticmethod
    def launch_queue_runner(queue):
        if isinstance(queue, Queue):
            return queue.launch_runner()
        else:
            raise TypeError('argument type error')

    def put(self, src_path, task_pattern):
        task_config = self.config["EXEC_TASK"].get(task_pattern, None)

        if task_config is None:
            return

        file_available = self.check_delay(src_path, task_config["delay"])
        queue_id = task_config["queue"]
        in_queue = self.is_in_queue(src_path, queue_id)
        is_in_running = self.is_in_running(src_path, queue_id)

        if not in_queue and file_available and not is_in_running:
            self.queue_ordered_dict[queue_id].put_task(
                src_path, task_pattern, task_config)

    def check_delay(self, src_path, delay):
        if (not isinstance(delay, int)) or (delay < 0):
            delay = self.config["SECS_DELAY_TO_PROCESS"]
        return self.mtime_age(src_path) > delay

    def is_in_queue(self, src_path, queue_id):
        queue = self.queue_ordered_dict.get(queue_id, None)

        return (queue and queue.is_in_queue(src_path))

    def is_in_running(self, src_path, queue_id):
        queue = self.queue_ordered_dict.get(queue_id, None)

        return (queue and queue.is_in_running(src_path))

    def go_through_queue(self, process_num):
        for q_id, q_obj in self.queue_ordered_dict.items():
            if not process_num:
                break

            while process_num:
                is_runner_launched = self.launch_queue_runner(q_obj)
                if is_runner_launched:
                    process_num -= 1
                else:
                    break

    def check_runner(self):
        count = 0
        for q in self.queue_ordered_dict.values():
            q.check_runner()
            count += q.count_of_running_tasks

        return count


class Queue(object):
    def __init__(self, queue_id, queue_config, dir_script):
        self.__running = {}
        self.id = queue_id
        self.priority = int(queue_config["priority"])
        self.max = queue_config["max"]
        self._queue = []
        self.__python = util.which('python')
        self.__dir_script = dir_script

    @property
    def qsize(self):
        return len(self._queue)

    @property
    def count_of_running_tasks(self):
        return len(self.__running)

    def put_task(self, src_path, task_pattern, task_config):
        # log.event("put_task:", src_path, task_pattern)
        self._queue.append([src_path, task_pattern, task_config])
        # log.event("put_task done", self._queue)

    def is_in_running(self, src_path):
        # log.diag("running length:", len(self.__running))
        return any([_f for _f in self.__running if _f == src_path])

    def is_in_queue(self, src_path):
        # log.diag("queue length:", len(self._queue))
        return any([_q for _q in self._queue if _q[0] == src_path])

    def launch_runner(self):
        # check MAX_NUM here
        # log.diag(self.count_of_running_tasks, " ", self.max)
        # log.diag("queue ", self.id)
        if self.count_of_running_tasks >= self.max or not self._queue:
            return False

        env = os.environ.copy()
        task = self._queue.pop(0)

        pattern = re.compile(task[1])
        src_path = task[0]
        mo = pattern.match(os.path.basename(src_path))

        settings = task[2]
        actions = settings.get('action')
        parallel = settings.get('parallel')
        self.__running.update({src_path: []})

        for action in actions:
            # lwsu@2018-0330
            # this must be in the loop or will be always replace
            # to last item
            kwargs = dict(env=env)

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

            try:
                args = [executable.decode('UTF-8') or self.__python.decode('UTF-8')]
            except:
                args = [executable or self.__python]

            if script_path:
                args.append(script_path)

            argument = action.get('argument')
            exec_args = mo.groupdict()
            exec_args.update({'FULL_PATH_FILENAME': src_path})
            if argument:
                argument = argument % exec_args
                args.append(argument)

            cwd = action.get('cwd')
            if cwd:
                kwargs['cwd'] = cwd
            else:
                kwargs['cwd'] = util.CWD

            sh = Shell(timeout=action.get("timeout"))

            self.__running[src_path].append(dict({
                "runner": sh,
                "keywords": exec_args,
                "settings": settings,
                "done": False,
                "exec": False,
                "parallel": parallel,
                "args": args,
                "kwargs": kwargs}))

        filedrives = self.__running[src_path]

        if parallel:
            self.launch_in_parallel(filedrives)
        else:
            self.launch_in_series(filedrives)

        return True

    def exec_filedrive(self, filedrive):
        sh = filedrive.get('runner')
        args = filedrive.get('args')
        kwargs = filedrive.get('kwargs')
        sh.run(*args, **kwargs)
        filedrive["exec"] = True

        log.event("ACTION executed, QueueID=", self.id,
                  ', PID=', sh.pid,
                  ", file=", filedrive["keywords"]["file"],
                  ", cmd={", sh.cmd, "}")

    def launch_in_parallel(self, filedrives):
        for filedrive in filedrives:
            self.exec_filedrive(filedrive)

    def launch_in_series(self, filedrives):

        for filedrive in filedrives:
            # filedrive was executed.
            if filedrive['exec'] is True:
                # filedrive is done, check next filedrive
                if filedrive['done'] is True:
                    continue
                # filedrive is running, don't exec another filedrive
                else:
                    break
            else:
                # execute this filedrives task
                self.exec_filedrive(filedrive)
                break

    def check_runner(self):
        tasks_done = []
        for src_path, filedrives in self.__running.items():
            # log.diag('running item: ', src_path, filedrives)
            is_done = True
            return_code = []
            is_parallel = None

            for idx, filedrive in enumerate(filedrives):
                is_parallel = filedrive.get('parallel')

                runner = filedrive['runner']
                if filedrive['exec'] and \
                        (not filedrive['done'] and runner.done()):
                    filedrive['done'] = True

                    if runner.returncode == 0:
                        log.event('ACTION done, QueueID=', self.id,
                                  ', PID=', runner.pid,
                                  ', file=', filedrive["keywords"]["file"],
                                  ', exit code=', runner.returncode)
                    elif runner.returncode == -9:
                        log.event('ACTION timeout, QueueID=', self.id,
                                  ', PID=', runner.pid,
                                  ', file=', filedrive["keywords"]["file"],
                                  ', exit code=', runner.returncode,
                                  ', cmd={', runner.cmd, '}',
                                  ', stdout={', runner.stdout, '}')
                    else:
                        log.event('ACTION error, QueueID=', self.id,
                                  ', PID=', runner.pid,
                                  ', file=', filedrive["keywords"]["file"],
                                  ', exit code=', runner.returncode,
                                  ', cmd={', runner.cmd, '}',
                                  ', stdout={', runner.stdout, '}',
                                  ', stderr={', runner.stderr, '}')

                is_done = is_done and filedrive['done']
                return_code.append(runner.returncode)

            if is_done:
                # log.diag("queue is done, return code: ", return_code)
                # returncode = 0 => success, returncode = 1/2/3/.. => fail
                is_success = not any(return_code)
                tasks_done.append({'path': src_path, 'is_success': is_success})
            else:
                # series filedrive task
                if not is_parallel:
                    self.launch_in_series(filedrives)

        self.archive_task(tasks_done)

    def archive_task(self, tasks_done):
        for task_done in tasks_done:
            src_path = task_done['path']

            filedrives = self.__running[src_path]
            filedrive = filedrives[0]
            settings = filedrive['settings']
            keywords = filedrive['keywords']

            success = settings['archive'].get('success')
            failure = settings['archive'].get('failure')

            if task_done['is_success']:
                paths_to = success  # or archive or basename
            else:
                paths_to = failure  # or archive or basename
            # if runner.returncode

            one_done = False

            if paths_to is False:
                one_done = True
            else:
                for path_to in paths_to:
                    if not path_to:
                        one_done = True
                        continue
                    dst_path = util.translate(path_to)
                    if keywords:
                        dst_path = dst_path % keywords
                    # dst_path = force_abs(base_to, dst_path)
                    if util.copy(src_path, dst_path):
                        one_done = True
                # for path_to

            # Todo: Should we purge file if one_done == False ???
            if one_done:
                util.purge(src_path)

            self.__running.pop(src_path)
