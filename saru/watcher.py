import logging
import os
import threading
import queue
import time
import webbrowser

import skia
import glfw
import pyautogui

from saru.overlay import Overlay
from saru.drawing import draw, draw_all_boxes
from saru.screenshots import take_screenshots, take_watch_screenshot, screen_changed
from saru.saru import process_image
from saru.vocabulary import save_vocabulary
from saru.strings import is_punctuation


class Watcher(threading.Thread):
    def __init__(self, options, recognizer, event_queue, overlay):
        threading.Thread.__init__(self)
        self._stop_flag = threading.Event()
        self._WATCH_MARGIN = 5  # TODO: magic number
        self._logger = logging.getLogger("saru")

        self._options = options
        self._recognizer = recognizer
        self._event_queue = event_queue
        self._overlay = overlay

        self._watch_path = None
        self._watch_region = None
        self._last_saru = None
        self._last_hover = None
        self._saved_clip = None

    def stop(self):
        self._stop_flag.set()

    def _handle_event(self, event):
        """Handles input events from the overlay"""
        if not event:
            return
        key = event.get_key()
        if key:
            self._logger.info(f"watcher got key event: {key}")
            self._handle_key(key)
        clip = event.get_clip()
        if clip:
            self._logger.info(f"watcher got clip event: {clip}")
            self._saved_clip = clip

    def _open_search(self, url):
        if self._last_hover:
            search_term = self._last_hover.surface()
        elif last_saru:
            search_term = self._last_saru["original"]
        if search_term:
            webbrowser.open(url + search_term)

    def _handle_key(self, key):
        match key:
            case glfw.KEY_C:
                self._overlay.clear()
            case glfw.KEY_D:
                self._options.debug = not self._options.debug
            case glfw.KEY_T:
                self._options.translate = not self._options.translate
            case glfw.KEY_J:
                self._open_search("http://jisho.org/search/")
            case glfw.KEY_W:
                self._open_search("https://ja.wikipedia.org/wiki/")
            case glfw.KEY_E:
                self._open_search("https://en.wikipedia.org/w/index.php?search=")
            case _:
                pass

    def _get_first_non_punct(self, saru):
        first_line = saru["cdata"][0]
        for cdata in first_line:
            if not is_punctuation(cdata.text):
                return cdata
        return None

    def _process(self):
        """Take a fresh screenshot and process it. if relevant, trigger drawing and update watch"""
        (full_path, text_path) = take_screenshots(
            self._options.NotesFolder, self._saved_clip
        )
        saru = process_image(self._options, self._recognizer, full_path, text_path)
        if saru:
            first_cdata = self._get_first_non_punct(saru)
            if first_cdata is None:
                first_cdata = saru["cdata"][0][0]
                self._logger.warn(
                    "failed to find non punctuation, using first character for watch: %s",
                    first_cdata,
                )
            self._watch_region = (
                self._saved_clip.x() + first_cdata.left + self._WATCH_MARGIN,
                self._saved_clip.y() + first_cdata.top + self._WATCH_MARGIN,
                first_cdata.width - self._WATCH_MARGIN * 2,
                first_cdata.height - self._WATCH_MARGIN * 2,
            )
            self._logger.debug("watch_region: %s", self._watch_region)
            self._watch_path = take_watch_screenshot(
                self._options.NotesFolder, self._watch_region
            )
            self._last_saru = saru
            self._overlay.draw(lambda c: draw(c, self._options, self._saved_clip, saru))

    def _update_hover(self):
        """Check if the mouse cursor is hovering over a token, and if so save the token"""
        if self._saved_clip and self._last_saru:
            hover = self._find_hover(self._saved_clip, self._last_saru["tokens"])
            if hover != self._last_hover:
                self._last_hover = hover
                self._logger.info(
                    f"hovered token: {hover.surface() if hover else None}"
                )

    def _find_hover(self, clip, tokens):
        for t in tokens:
            if self._is_mouse_inside(clip, t.box()):
                return t
        return None

    def _is_mouse_inside(self, clip, rect):
        shifted = skia.Rect.MakeXYWH(
            clip.x() + rect.x(), clip.y() + rect.y(), rect.width(), rect.height()
        )
        pos = pyautogui.position()
        pixel = skia.Rect.MakeXYWH(pos.x, pos.y, 1, 1)
        return shifted.intersect(pixel)

    def run(self):
        """Primary watch loop, periodically takes screenshots and reprocesses text"""
        while not self._stop_flag.is_set():
            try:
                event = self._event_queue.get(timeout=0.5)
            except queue.Empty:
                event = None
            self._handle_event(event)
            changed = self._has_screen_changed()
            if self._saved_clip and (not self._watch_path or changed or event):
                self._overlay.clear(block=True)
                self._process()
            self._update_hover()

    def _has_screen_changed(self):
        if self._options.no_watch:
            return False
        if not self._watch_region or not self._watch_path:
            return False
        return screen_changed(
            self._options.NotesFolder, self._watch_path, self._watch_region
        )
