import os
import json
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


def get_path(notes_folder, base, extension, title=None, dated=False, timed=False):
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
    path = os.path.join(notes_folder, filename)
    path = os.path.expanduser(path)
    return os.path.normpath(path)
