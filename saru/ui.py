import logging
import os
import threading
import time
import webbrowser
import tempfile
from queue import SimpleQueue

import skia
import glfw
import pyautogui

from saru.overlay import Overlay
from saru.screenshots import take_screenshots, take_watch_screenshot, screen_changed
from saru.vocabulary import save_vocabulary
from saru.watcher import Watcher


_logger = logging.getLogger("saru")


def main_loop(options, recognizer):
    event_queue = SimpleQueue()
    overlay = Overlay("saru", event_queue)
    with tempfile.TemporaryDirectory() as temp_dir:
        watcher = Watcher(options, recognizer, event_queue, overlay, temp_dir)
        watcher.start()
        try:
            overlay.ui_loop()
        finally:
            watcher.stop()
        watcher.join()
