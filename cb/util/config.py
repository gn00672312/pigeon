# -*- coding: utf-8 -*-
import os


class ConfigError(Exception):
    def __init__(self, levels, msg):
        self.message = '%s: %s' % ('/'.join(levels), msg)

    def __str__(self):
        return self.message


def get_abs_path(config_file):
    if not os.path.isabs(config_file):
        conf_path = os.environ.get("CONF", 'conf')
        OPERATION_MODE = os.environ.get("OPERATION_MODE", None)
        if OPERATION_MODE:
            _config_file = os.path.join(conf_path, OPERATION_MODE, config_file)
            if os.path.exists(_config_file):
                config_file = _config_file
            else:
                # OPERATION_MODE 裏找不到, 就回頭找 CONF 根目錄
                config_file = os.path.join(conf_path, config_file)
        else:
            config_file = os.path.join(conf_path, config_file)

    if not os.path.exists(config_file):
        raise ConfigError(['exec'], 'config file does not exist: %s' %
                          config_file)
    return config_file


def load(config_file):
    config_file = get_abs_path(config_file)

    config = {}
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
            raise ConfigError(['exec'],
                              'Error during importing config: %s' % config_file)

    except Exception:
        raise ConfigError(['exec'],
                          'Error during importing config: %s' % config_file)
