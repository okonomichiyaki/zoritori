import json
import logging
import os
import sys
from pathlib import Path

import zoritori.pipeline
import zoritori.ui as ui
from zoritori.options import get_options
from zoritori.files import start_new_session


def configure_logging(log_level):
    logger = logging.getLogger("zoritori")
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    if log_level == "debug":
        ch.setLevel(logging.DEBUG)
    else:
        ch.setLevel(logging.INFO)
    formatter = logging.Formatter("%(levelname)s - %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)


def main():
    options = get_options()

    configure_logging(options.log_level)

    if not options.NotesFolder and options.NotesRoot:
        prefix = options.NotesPrefix or "session"
        options.NotesFolder = start_new_session(options.NotesRoot, prefix)
    elif options.NotesFolder:
        path = Path(options.NotesFolder)
        path.mkdir(parents=True, exist_ok=True)
        options.NotesFolder = path

    if options.Engine == "google":
        if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
            print("No Google Cloud environment variable found")
            exit(1)
        from zoritori.recognizers.google_vision import Recognizer

        recognizer = Recognizer()
    elif options.Engine == "tesseract":
        from zoritori.recognizers.tesseract import Recognizer

        recognizer = Recognizer(options.TesseractExePath)

    ui.main_loop(options, recognizer)
