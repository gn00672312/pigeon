# -*- coding: utf-8 -*-

from __future__ import (
    absolute_import,
)
import os
import re
import errno
import shutil
import datetime
from .shell import Shell

from module import log

CWD = os.getcwd()
FORMAT = 'format'
YMDHMS = '%Y%m%d%H%M%S'
TIMESTAMP_UTC = re.compile(r'\{timestamp_utc(\|(?P<format>[^ }]+))*}')
TIMESTAMP_LST = re.compile(r'\{timestamp_lst(\|(?P<format>[^ }]+))*}')


class ConfigError(Exception):
    def __init__(self, levels, msg):
        self.message = '%s: %s' % ('/'.join(levels), msg)

    def __str__(self):
        return self.message


def read_conf(config_file):
    config = {}
    if not os.path.isabs(config_file):
        config_file = os.path.abspath(config_file)

    if not os.path.exists(config_file):
        raise ConfigError(['exec'], 'config file does not exist: %s' %
                          config_file)
    log.event('Reading configuration file: ', config_file)

    # for python 3
    try:
        with open(config_file) as f:
            exec(f.read(), {}, config)
        return config

    # for python 2.7
    except NameError:
        try:
            execfile(config_file, {}, config)
            return config
        except Exception:
            log.exception('Error during importing config: ', config_file)
            raise ConfigError(['exec'],
                              'Error during importing config: %s' % config_file)

    except Exception:
        log.exception('Error during importing config: ', config_file)
        raise ConfigError(['exec'],
                          'Error during importing config: %s' % config_file)


def assert_type(value, value_type, levels):
    if value is None or not isinstance(value, value_type):
        if not isinstance(value_type, (list, tuple)):
            err_msg = 'must be %s.' % value_type.__name__
        else:
            err_msg = 'must be one of %s.' % ', '.join(
                [i.__name__ for i in value_type])
        raise ConfigError(levels, err_msg)


def extract_config(config, key, value_type, mandatory, parents=None):
    levels = [key]

    if isinstance(parents, (list, tuple)):
        levels = parents + levels

    if mandatory and key not in config:
        raise ConfigError(levels, 'not set.')

    o = object()
    value = config.get(key, o)
    if value == o:
        return None

    assert_type(value, value_type, levels)
    return value


def extract_config_wrapper(config, default_configs, arg_name, parents=None):
    default_config = default_configs[arg_name]
    val = extract_config(config, arg_name,
                         default_config['type'],
                         default_config['mandatory'],
                         parents)

    # has default value
    # if default_config['val'] and val is None:
    #     val = default_config['val']

    # some argument's default is empty...
    if val is None:
        val = default_config['val']

    return val


def check_and_set_default_config(target_config, default_configs,
                                 parents=None, base=CWD):
    """
    確認 target config 設置是否正確，以及當有些 option 沒寫，會填入預設值資料

    :param target_config: 目標的要修改的 config (dict)
    :param default_configs: 預設 config (dict)
    :param parents: 主要用來設定 log level 用
    :param base: base dir
    :return:
    """
    config = {}

    for arg_name, default_conf in default_configs.items():
        val = extract_config_wrapper(target_config, default_configs, arg_name, parents)
        config[arg_name] = val

        # check abs path
        if default_conf.get('is_path', False):
            if isinstance(val, bool):
                pass
            elif isinstance(val, (tuple, list)):
                config[arg_name] = []
                for v in val:
                    config[arg_name].append(force_abs(base, v) if v else base)
            else:
                config[arg_name] = force_abs(base, val) if val else base

        # check min value
        lvl = [arg_name]
        min_val = default_conf.get('min_value', None)
        if isinstance(parents, (list, tuple)):
            lvl = parents + lvl

        check_min_value(min_val, val, lvl)

    return config


def check_min_value(min_val, val, err_lvl):

    # check min value
    if min_val is not None and not val == -99 and val < min_val:
        msg = 'must be an integer with value >= %s' % min_val
        raise ConfigError(err_lvl, msg)

    return val


def force_abs(dir_base, path):
    try:
        if not os.path.isabs(path):
            path = os.path.join(dir_base, path)
    except:
        # log.exception()
        raise
    return path


def scan(directory, recursive=True):
    """
    Scan files in the specified directory. The returned entries are
    relative path to the given directory.
    """
    here = os.getcwd()
    directory = os.path.abspath(directory)
    if here != directory:
        try:
            os.chdir(directory)
        except:
            log.problem('Cannot change working directory to ', directory)
            return []

    file_list = []

    for root, dirs, files in os.walk('.'):
        if recursive or os.path.abspath(root) == directory:
            for name in files:
                file_list.append(os.path.normpath(os.path.join(directory, root, name)))

    # Fall back to original directory.
    os.chdir(here)
    return file_list


def sort_by_mtime(file_list, reverse=False):
    # Lambda function to sort file by mtime.
    # sort_key = lambda x: os.path.getmtime(x)
    def sort_key(path):
        try:
            return os.path.getmtime(path)
        except FileNotFoundError:
            # 這裡有可能會找不到檔案(不知何種原因) 只好傳回0.0
            return 0.0

    return sorted(file_list, key=sort_key, reverse=reverse)


def copy(path_from, path_to):
    try:
        if path_to != os.path.devnull:
            makedirs(os.path.dirname(path_to))
            # if os.path.exists(path_to):
            #    os.remove(path_to)
            shutil.copy(path_from, path_to)
        log.event('File copied: ', path_from, ' --> ', path_to)
        return True
    except:
        log.exception('Error copying file: ', path_from, ' --> ', path_to)
        return False


def purge(file_path):
    try:
        os.remove(file_path)
        log.event('File deleted: ', file_path)
    except Exception as e:
        if isinstance(e, OSError) and e.errno == errno.ENOENT:
            log.event('File deleted by other process: ', file_path)
        else:
            log.exception('Cannot delete file: ', file_path)


def strftime(dtime, dtime_format):
    """
    Custom, extended, version for the datetime.strftime() to has the
    following capabilities:

     -- %3f
        Millisecond as a decimal number [0, 999], zero-padded on the left.
     -- %-3f
        Millisecond as a decimal number [0, 999], no zero-padded on the
        left.
    """
    assert isinstance(dtime, (datetime.date, datetime.time,
                              datetime.datetime))

    result = ''
    num_ignore = 0
    last = len(dtime_format) - 1
    for i, s in enumerate(dtime_format):
        if num_ignore > 0:
            num_ignore -= 1
            continue
        if s == '%' and i != last:
            if dtime_format[i + 1] == '%':
                num_ignore = 1
                result += '%%'
            elif dtime_format[i + 1: i + 3] == '3f':
                num_ignore = 2
                result += dtime.strftime('%f')[:3]
            elif dtime_format[i + 1: i + 4] == '-3f':
                num_ignore = 3
                result += str(getattr(dtime, 'microsecond', 0))
            else:
                num_ignore = 0
                result += s
        else:
            result += s
    return dtime.strftime(result)


def translate(tag):
    """
    Parse the given name and translate all tags begin by '{' and end by '}'.
    Currently we support the following tag translation:

     -- {timestamp_lst|format}
     -- {timestamp_utc|format}
        Here the 'format' uses datetime.strftime specs and extend
        '%3f' to be the millisecond. If 'format' is omitted, uses
        '%Y-%m-%d %H:%M:%S' as default. Also the '|' sign can't appear
        there in such case.
    """
    def trans_timestamp(string):
        timestamp_lst = datetime.datetime.now()
        timestamp_utc = timestamp_lst - datetime.timedelta(hours=8)
        mo = TIMESTAMP_UTC.search(string)
        if mo:
            dtime_format = mo.groupdict().get(FORMAT) or YMDHMS
            timestamp = strftime(timestamp_utc, dtime_format)
            string = re.sub(TIMESTAMP_UTC, timestamp, string)
        mo = TIMESTAMP_LST.search(string)
        if mo:
            dtime_format = mo.groupdict().get(FORMAT) or YMDHMS
            timestamp = strftime(timestamp_lst, dtime_format)
            string = re.sub(TIMESTAMP_LST, timestamp, string)
        return string

    result = trans_timestamp(tag)
    return result


def makedirs(dir_path, mode=0o755):
    try:
        if not os.path.isabs(dir_path):
            dir_path = os.path.abspath(dir_path)
        os.makedirs(dir_path, mode)
    except Exception as e:
        if not isinstance(e, OSError) or e.errno != errno.EEXIST:
            log.exception('Cannot create directory: ', dir_path)
    else:
        log.event('Directory created: ', dir_path)


def which(executable):
    """
    Search where the given executable resides.
    """
    sh = Shell()
    sh.run('which', executable).wait()
    return sh.stdout or executable
