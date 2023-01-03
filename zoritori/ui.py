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

from zoritori.overlay import Overlay
from zoritori.screenshots import take_screenshots, take_watch_screenshot, screen_changed
from zoritori.vocabulary import save_vocabulary
from zoritori.watcher import Watcher


_logger = logging.getLogger("zoritori")


def main_loop(options, recognizer):
    event_queue = SimpleQueue()
    overlay = Overlay("zoritori", event_queue)
    with tempfile.TemporaryDirectory() as temp_dir:
        watcher = Watcher(options, recognizer, event_queue, overlay, temp_dir)
        watcher.start()
        try:
            overlay.ui_loop()
        finally:
            watcher.stop()
        watcher.join()