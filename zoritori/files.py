import os
import re
import json

from pathlib import Path
from datetime import datetime
from json.decoder import JSONDecodeError


def load_json(path):
    if path.exists():
        with path.open() as f:
            try:
                return json.load(f)
            except JSONDecodeError:
                return None
    return None


def save_json(path, data):
    with path.open("w") as f:
        json.dump(data, f)


def _get_session_id(prefix, s):
    p = re.compile(prefix + "([0-9]+)")
    m = p.match(s)
    if m:
        return int(m.groups()[0])
    else:
        return -1


def start_new_session(root_dir, prefix):
    children = next(os.walk(root_dir))[1]
    sessions = [_get_session_id(prefix, child) for child in children]
    if len(sessions) == 0:
        last_session = -1
    else:
        last_session = max(sessions)
    new_session = "{:03d}".format(last_session + 1)
    path = Path(root_dir) / (prefix + new_session)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_path(folder, base, extension, title=None, dated=False, timed=False):
    filename = base
    if dated:
        date = datetime.now().strftime("%Y-%m-%d")
        filename = filename + "-" + date
    if timed:
        # time = datetime.now().strftime("T%H-%M-%S")
        time = datetime.now().strftime("T%H%M%S_%f")[:-3]
        filename = filename + "-" + time
    if title:
        filename = filename + "-" + title
    filename = filename + "." + extension
    path = os.path.join(folder, filename)
    path = os.path.expanduser(path)
    return os.path.normpath(path)
