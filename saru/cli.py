import json
import logging
import os
import sys

import saru.saru
import saru.ui as ui
from saru.options import get_options


def configure_logging(log_level):
    logger = logging.getLogger("saru")
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
        from saru.recognizers.google_vision import Recognizer

        recognizer = Recognizer()
    elif options.engine == "tesseract":
        from saru.recognizers.tesseract import Recognizer

        recognizer = Recognizer(options.TesseractExePath)

    if options.filename:
        data = saru.saru.process_image_light(options, recognizer)
        if not options.debug:
            sys.stdout.reconfigure(encoding="utf-8", newline="\n")
            print(json.dumps(data))
    else:
        ui.main_loop(options, recognizer)
