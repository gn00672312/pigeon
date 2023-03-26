# -*- coding: utf-8 -*-
from __future__ import (absolute_import)
import os
import re
from time import sleep, time

from .cb_queue import QueueManager
from . import util
from .process import Process

from module import log

DEFAULT_ARGS = {
    'DIR_MONITOR': {
        'val': '/data/import',
        'type': str,
        'mandatory': False,
        'is_path': True
    },
    'DIR_ARCHIVE': {
        'val': '/data/archive',
        'type': str,
        'mandatory': False,
        'is_path': True
    },
    'DIR_ARCHIVE_SUCCESS': {
        'val': '/data/archive',
        'type': str,
        'mandatory': False,
        'is_path': True
    },
    'DIR_ARCHIVE_FAILURE': {
        'val': '/data/archive',
        'type': str,
        'mandatory': False,
        'is_path': True
    },
    'DIR_ARCHIVE_UNKNOWN': {
        'val': '/data/archive',
        'type': str,
        'mandatory': False,
        'is_path': True
    },
    'DIR_SCRIPT': {
        'val': '',
        'type': str,
        'mandatory': False,
        'is_path': True
    },
    'NUM_MAX_PROCESSOR': {
        'val': 10,
        'type': int,
        'mandatory': False,
        'min_value': 1
    },
    'SECS_DELAY_TO_PROCESS': {
        'val': 60,
        'type': int,
        'mandatory': False,
        'min_value': 5,
    },
    'SECS_TIMEOUT_FOR_ACTION':  {
        'val': 0,
        'type': int,
        'mandatory': False,
        'min_value': 0,
    },
    'EXEC_TASK': {
        'val': {},
        'type': dict,
        'mandatory': False
    },
    'MOVE_TASK': {
        'val': {},
        'type': dict,
        'mandatory': False
    },
    'QUEUE': {
        'val': {},
        'type': dict,
        'mandatory': True
    },
}

DEFAULT_EXEC_TASK = {
    'delay': {
        'val': -99,
        'type': int,
        'mandatory': False,
        'min_value': 5,
    },
    'action': {
        'val': [],
        'type': (list, tuple),
        'mandatory': True
    },
    'parallel': {
        'val': False,
        'type': bool,
        'mandatory': False
    },
    'archive': {
        'val': {},
        'type': dict,
        'mandatory': False
    },
    'queue': {
        'val': '',
        'type': str,
        'mandatory': True,
    },
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

"""
val = True -> get default dir (DIR_ARCHIVE in config)
"""
DEFAULT_ARCHIVE = {
    'default': {
        'val': True,
        'type': (bool, list, tuple),
        'mandatory': False,
        'is_path': True
    }
}

"""
val = True -> get default dir (DIR_ARCHIVE in config)
"""
DEFAULT_ARCHIVE_SUCCESS = {
    'success': {
        'val': True,
        'type': (bool, list, tuple),
        'mandatory': False,
        'is_path': True
    }
}

"""
val = True -> get default dir (DIR_ARCHIVE in config)
"""
DEFAULT_ARCHIVE_FAILURE = {
    'failure': {
        'val': True,
        'type': (bool, list, tuple),
        'mandatory': False,
        'is_path': True
    }
}

DEFAULT_QUEUE = {
    'priority': {
        'val': '',
        'type': int,
        'mandatory': True,
        'min_value': 1,
    },
    'max': {
        'val': '',
        'type': int,
        'mandatory': True,
        'min_value': 1,
    }
}

DEFAULT_MOVE_TASK = {
    'delay': DEFAULT_ARGS['SECS_DELAY_TO_PROCESS'],
    'path': {
        'val': '',
        'type': (list, tuple, str),
        'mandatory': True,
        'is_path': True
    }
}


class FileDrive(Process):
    (EXEC_TASK,
     MOVE_TASK,
     UNKNOWN) = range(3)

    def __init__(self, config_file=None):
        super(FileDrive, self).__init__(config_file)
        self.config = None
        self.qm = None
        if config_file is not None:
            self.load_config()

    def load_config(self):
        if self.need_reload_config:
            self.config = self.import_config(self.config_file)
            self.qm = QueueManager(self.config)
            self.need_reload_config = False

    @staticmethod
    def is_match(file_path, pattern):
        return re.match(pattern, os.path.basename(file_path))

    def get_pattern(self, file_path):
        for pattern in self.config["EXEC_TASK"]:
            mo = self.is_match(file_path, pattern)
            if mo:
                return self.EXEC_TASK, pattern, mo
        for pattern in self.config["MOVE_TASK"]:
            mo = self.is_match(file_path, pattern)
            if mo:
                return self.MOVE_TASK, pattern, mo
        return self.UNKNOWN, None, None

    def startup(self, timeout=None):
        self.load_config()
        max_num = self.config["NUM_MAX_PROCESSOR"]
        start = time()
        while not self.TERMINATING:
            # Here, we check runner first, because it will archive the file
            # that has completed and reduce the file numbers in the monitor dir
            count = self.qm.check_runner()
            if timeout is not None and time() - start > timeout:
                break
            self.go_through_files(
                util.sort_by_mtime(util.scan(self.config["DIR_MONITOR"])))
            if count < max_num:
                self.qm.go_through_queue(max_num-count)
            sleep(1)

    @staticmethod
    def mtime_age(path):
        """
        lwsu@2018-10-16
          從 cb_queue copy 過來的... 沒辦法...
        """
        try:
            return time() - os.path.getmtime(path)
        except:
            log.exception(path)
            # No age no matter why we can't get mtime.
            return 0

    def check_delay(self, src_path, delay):
        """
        lwsu@2018-10-16
          從 cb_queue copy 過來的... 沒辦法...
        """
        if (not isinstance(delay, int)) or (delay < 0):
            delay = self.config["SECS_DELAY_TO_PROCESS"]
        return self.mtime_age(src_path) > delay

    def go_through_files(self, file_list):
        for f in file_list:
            # 雖然在go_through_files之前scan過檔案了,但還是發生過沒檔案的情況
            if not os.path.exists(f):
                continue
            task_code, pattern, mo = self.get_pattern(f)
            # log.debug("go_through_files ", f, " task_code=", task_code)

            if task_code == self.UNKNOWN:
                if self.check_delay(f, None):
                    # move unknown file to somewhere
                    log.event("UNKNONW file: ", f)
                    self.__run_move_unknown(f)

            elif task_code == self.MOVE_TASK:
                move_task_config = self.config["MOVE_TASK"].get(pattern)
                if self.check_delay(f, move_task_config.get("delay", None)):
                    # move file
                    # lwsu@2018-10-16
                    #  這裏也需要 check delay，檔案只要傳輸久一點，就會 move 不完整的檔
                    log.event("MOVE file: ", f)
                    self.__run_move(f, pattern, mo.groupdict())

            else:
                # pattern in EXEC_TASK
                self.qm.put(f, pattern)

    def __run_move(self, src_file, pattern, keywords):
        task_config = self.config["MOVE_TASK"].get(pattern)
        path_from = src_file
        paths_to = task_config["path"]
        try:
            if not isinstance(paths_to, (list, tuple)):
                paths_to = [paths_to]

            at_least_one_done = False
            for path_to in paths_to:
                path_to = util.translate(path_to)
                if keywords:
                    path_to = path_to % keywords
                path_to = util.force_abs(self.config["DIR_ARCHIVE"], path_to)
                if util.copy(path_from, path_to):
                    at_least_one_done = True

            # Purge file if at least one copy success.
            if at_least_one_done:
                util.purge(path_from)
        except:
            log.exception('Move task failed: ', path_from)

    def __run_move_unknown(self, src_file):
        path_from = src_file

        _, file_name = os.path.split(src_file)
        path_to = os.path.join(self.config["DIR_ARCHIVE_UNKNOWN"], file_name)
        try:
            util.copy(path_from, path_to)

            # Purge file
            util.purge(path_from)
        except:
            log.exception('Move unknown file failed: ', path_from)

    @classmethod
    def import_config(cls, config_file):
        _config = util.read_conf(config_file)
        config = util.check_and_set_default_config(_config, DEFAULT_ARGS)

        cls._import_queue_config(config)
        cls._import_task_config(config)
        cls._import_move_config(config)

        return config

    @classmethod
    def _import_queue_config(cls, config):
        for queue_id, queue_config in config['QUEUE'].items():
            _queue_config = util.check_and_set_default_config(queue_config, DEFAULT_QUEUE,
                                                              ['QUEUE', queue_id])
            queue_config.update(_queue_config)

    @classmethod
    def _import_task_config(cls, config):
        for task_pattern, task_config in config['EXEC_TASK'].items():
            # check exec task arguments type and assign to config
            _task_config = util.check_and_set_default_config(
                task_config, DEFAULT_EXEC_TASK,
                ['EXEC_TASK', task_pattern])

            if _task_config['delay'] == -99:
                _task_config['delay'] = config["SECS_DELAY_TO_PROCESS"]

            task_config.update(_task_config)
            if task_config['queue'] not in config['QUEUE']:
                lvl = ['EXEC_TASK', 'queue']
                msg = 'queue "' + task_config['queue'] + '" does not exist.'
                raise util.ConfigError(lvl, msg)

            for action in task_config['action']:
                # check exec task action arguments type and assign to config
                action_config = util.check_and_set_default_config(
                    action, DEFAULT_ACTION, ['EXEC_TASK', 'action'])
                action.update(action_config)
                executable = action_config['executable']
                script = action_config['script']

                if action['timeout'] == -99:
                    action['timeout'] = config["SECS_TIMEOUT_FOR_ACTION"]

                # special check config
                # executable must be either absolute or basename.
                if executable:
                    if (os.path.basename(executable) != executable and
                            not os.path.isabs(executable)):
                        lvl = ['EXEC_TASK', 'action', 'executable']
                        msg = 'must be either absolute or only basename.'
                        raise util.ConfigError(lvl, msg)

                # Either executable or script must be provided.
                if not executable and not script:
                    lvl = ['EXEC_TASK', 'action']
                    msg = 'either "executable" or "script" must be set.'
                    raise util.ConfigError(lvl, msg)

            archive_config = {}
            # check exec task archive arguments type and assign to config
            archive_default = util.check_and_set_default_config(
                task_config['archive'], DEFAULT_ARCHIVE,
                ['EXEC_TASK', 'archive'],
                config['DIR_ARCHIVE'])
            archive_success = util.check_and_set_default_config(
                task_config['archive'], DEFAULT_ARCHIVE_SUCCESS,
                ['EXEC_TASK', 'archive_success'],
                config['DIR_ARCHIVE_SUCCESS'])
            archive_failure = util.check_and_set_default_config(
                task_config['archive'], DEFAULT_ARCHIVE_FAILURE,
                ['EXEC_TASK', 'archive_failure'],
                config['DIR_ARCHIVE_FAILURE'])
            archive_config.update(archive_default)
            archive_config.update(archive_success)
            archive_config.update(archive_failure)

            if archive_config['default'] is True:
                archive_config['default'] = [config['DIR_ARCHIVE']]

            if archive_config['success'] is True:
                archive_config['success'] = archive_config['default']

            if archive_config['failure'] is True:
                archive_config['failure'] = archive_config['default']

            task_config['archive'].update(archive_config)

    @classmethod
    def _import_move_config(cls, config):
        for move_pattern, move_config in config['MOVE_TASK'].items():
            _move_config = util.check_and_set_default_config(
                move_config, DEFAULT_MOVE_TASK, ['MOVE_TASK', move_pattern])
            move_config.update(_move_config)


if __name__ == '__main__':
    filedrive = FileDrive('filedrive.conf')
    # filedrive.install_signal_handlers()
    filedrive.startup()
