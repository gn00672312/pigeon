import os
import sys

PROGRAM_PATH = os.path.abspath(__file__)
PROGRAM_NAME = os.path.basename(PROGRAM_PATH)
if PROGRAM_NAME.endswith(".py"):
    PROGRAM_NAME = PROGRAM_NAME[:-3]

BASE_DIR = os.path.dirname(os.path.dirname(PROGRAM_PATH))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from dotenv import load_dotenv

load_dotenv()

from module.util.config import get_conf_abs_path
from module.daemon.timedrive import TimeDrive
from module.daemon.service import LinuxService

from module import log

log.set_log_config(get_conf_abs_path("log.timedrive.conf"))
log.verbose("using config log.timedrive.conf")

CONFIG_NAME = os.environ.get('TIMEDRIVE_CONF', 'timedrive.conf')

if __name__ == "__main__":
    program_dir = os.path.dirname(PROGRAM_PATH)
    pid_file = os.path.join(program_dir, '.%s.pid' % PROGRAM_NAME)
    config_file = get_conf_abs_path(CONFIG_NAME)
    log.diag("config file : ", config_file)
    timedrive = TimeDrive(config_file=config_file)
    timedrive_service = LinuxService(
        service_process=timedrive,
        program_path=PROGRAM_PATH,
        pid_file=pid_file
    )
