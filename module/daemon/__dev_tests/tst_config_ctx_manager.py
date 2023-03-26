import os
import sys

CONFIG_TMP = "tst_filedrive.conf"
CONFIG_POOR = "filedrive.conf"

PATH = os.path.dirname(os.path.abspath(__file__))


class TstConfigCtxManager():
    def __init__(self, titles, tmp=None):
        config_tmp = CONFIG_TMP if tmp is None else tmp
        self.titles = titles
        self.config_filename = config_tmp
        if os.path.exists(self.config_filename):
            os.remove(self.config_filename)

    def __enter__(self):
        lines = read_conf(self.titles)
        write_conf(self.config_filename, lines)
        return self.config_filename

    def __exit__(self, type, value, traceback):
        if os.path.exists(self.config_filename):
            os.remove(self.config_filename)


def read_conf(titles, poor=None):
    config_poor = CONFIG_POOR if poor is None else poor
    match = False
    lines = []
    with open(os.path.join(PATH, config_poor), 'rt') as fin:
        for line in fin:
            if line.startswith("##"):
                line = line[2:].strip()
                match = line in titles
            elif match:
                lines.append(line)

    return lines


def write_conf(filename, lines):
    with open(filename, 'w') as fout:
        fout.write("".join(lines))


if __name__ == "__main__":
    # lines = read_conf(['SYNTAX_ERROR', 'TASK_HAS_ONLY_SCRIPT'])
    # write_conf('test_conf.conf', lines)

    titles = ["EMPTY"]
    with TstConfigCtxManager(titles) as cf:
        print(cf)
