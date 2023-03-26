# -*- coding: utf-8 -*-
import os
import sys
import time
import glob
import shutil

import click

PROGRAM_PATH = os.path.abspath(__file__)
BASE_DIR = os.path.dirname(os.path.dirname(PROGRAM_PATH))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)
from dotenv import load_dotenv

load_dotenv()

from module import log
from module.util.config import get_conf_abs_path, load_config

log.set_log_config(get_conf_abs_path("log.bin.conf"))


def run_clean_path(conf_file, dry_run):
    CLEAN_CONF = load_config(conf_file)
    file_number = 0

    # check each conf in pattern
    for conf in CLEAN_CONF['CLEAR_PATH']:
        path_pattern = conf['path_pattern']
        expiration = conf['expiration']

        # check path and expiration
        if path_pattern is None or expiration is None:
            return

        # 先找到過期檔案
        match_files = []
        for target_file in glob.glob(path_pattern):
            for dir_path, dir_names, file_names in os.walk(target_file):
                for f in file_names:
                    fp = os.path.join(dir_path, f)
                    if is_expired(fp, expiration):
                        match_files.append(fp)
                for d in dir_names:
                    dp = os.path.join(dir_path, d)
                    if is_expired(dp, expiration):
                        match_files.append(dp)

        match_files.sort(reverse=True)
        if dry_run:
            for _file in match_files:
                log.verbose("match file", _file)

        else:
            for file_path in match_files:
                try:
                    if os.path.isdir(file_path) and len(os.listdir(file_path)) == 0:
                        shutil.rmtree(file_path)
                        log.verbose("remove dir", file_path)
                        file_number += 1
                    elif not os.path.isdir(file_path):
                        os.remove(file_path)
                        log.verbose("remove file", file_path)
                        file_number += 1

                except OSError:
                    log.exception()

            log.debug((
                "remove {path_pattern} expiration "
                "in {expiration} hours is done!"
                "\ntotal clear file number: {file_number}"
            ).format(
                path_pattern=path_pattern,
                expiration=expiration,
                file_number=file_number)
            )


def is_expired(filename, expiration):
    delta = (time.time() - os.path.getmtime(filename))
    return delta > (float(expiration) * 60 * 60)


CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.command(context_settings=CONTEXT_SETTINGS)
@click.option('--conf_file', '-c',
              default="clean_path.conf",
              help="clean the conf path pattern files")
@click.option('--dry-run', is_flag=True,
              default=False,
              help="clean the conf path pattern files")
def main(conf_file, dry_run):
    try:
        if not os.path.exists(get_conf_abs_path(conf_file)):
            raise Exception('incorrect conf file path....')
        run_clean_path(conf_file, dry_run)
    except:
        log.exception()
        sys.exit(1)


if __name__ == "__main__":
    main()
