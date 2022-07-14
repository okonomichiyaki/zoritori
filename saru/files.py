import os
from datetime import datetime


def get_path(notes_folder, base, extension, title=None, dated=False, timed=False):
    filename = base
    if dated:
        date = datetime.now().strftime("%Y-%m-%d")
        filename = filename + "-" + date
    if timed:
        #time = datetime.now().strftime("T%H-%M-%S")
        time = datetime.now().strftime("T%H%M%S_%f")[:-3]
        filename = filename + "-" + time
    if title:
        filename = filename + "-" + title
    filename = filename + "." + extension
    path = os.path.join(notes_folder, filename)
    path = os.path.expanduser(path)
    return os.path.normpath(path)
