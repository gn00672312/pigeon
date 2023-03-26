import os
import json

from .config import load as load_config


def emit(spec, opts=None):
    filedrive_conf = load_config("filedrive.conf")
    import_dir = filedrive_conf['DIR_MONITOR']

    if not os.path.exists(import_dir):
        os.makedirs(import_dir)
    file_path = os.path.join(import_dir, spec)
    if not os.path.exists(file_path):
        with open(file_path, 'w') as f:
            if opts is None:
                # Just creation.
                pass
            else:
                # Add arguments to singal file.
                f.write(json.dumps(opts))
    return file_path
