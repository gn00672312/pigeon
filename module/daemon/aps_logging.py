# -*- coding: utf-8 -*-
import os
import logging

HOME = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOG_DIR = os.environ.get("LOG_DIR", os.path.join(HOME, 'logfiles'))
LOG_FILENAME = os.path.join(LOG_DIR, 'general.log')


def set_log_config(file_path=None):
    # Remove all handlers associated with the root logger object.
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    if not file_path:
        file_path = LOG_FILENAME

    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%m-%d-%Y %H:%M:%S',
                        handlers=[logging.FileHandler(file_path, 'a+', 'utf-8'), ])

    # console = logging.StreamHandler()
    # console.setLevel(logging.INFO)
    # formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    # console.setFormatter(formatter)
    # logging.getLogger('').addHandler(console)


set_log_config()
