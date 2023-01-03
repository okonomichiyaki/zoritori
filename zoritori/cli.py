import json
import logging
import os
import sys
from pathlib import Path

import zoritori.pipeline
import zoritori.ui as ui
from zoritori.options import get_options


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

    if options.engine == "google":
        if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
            print("No Google Cloud environment variable found")
            exit(1)
        from zoritori.recognizers.google_vision import Recognizer

        recognizer = Recognizer()
    elif options.engine == "tesseract":
        from zoritori.recognizers.tesseract import Recognizer

        recognizer = Recognizer(options.TesseractExePath)

    if options.filename:
        data = zoritori.pipeline.process_image_light(
            options.filename, options, recognizer
        )
        if not options.debug:
            sys.stdout.reconfigure(encoding="utf-8", newline="\n")
            print(json.dumps(data))
    else:
        if options.NotesFolder and len(options.NotesFolder) > 0:
            Path(options.NotesFolder).mkdir(parents=True, exist_ok=True)
        ui.main_loop(options, recognizer)
