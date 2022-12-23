import logging
import os
import threading
import queue
import time
import webbrowser
from pathlib import Path
from math import trunc

import skia
import glfw
import pyautogui

from saru.overlay import Overlay
from saru.drawing import draw
from saru.screenshots import (
    take_screenshots,
    take_watch_screenshot,
    screen_changed,
    take_screenshot_clip_only,
)
from saru.saru import process_image, process_image_light
from saru.vocabulary import save_vocabulary
from saru.strings import is_punctuation
from saru.files import load_json, save_json


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

        self._watch_paths = None
        self._watch_regions = None
        self._last_sdata = None
        self._last_hover = None
        self._saved_clip = None
        self._secondary_clip = None
        self._clips_path = Path.home() / ".saru" / "clips.json"

    def stop(self):
        self._stop_flag.set()

    def _handle_event(self, event):
        """Handles input events from the overlay"""
        if not event:
            return
        clip = event.get_clip()
        key = event.get_key()
        if clip and key == glfw.KEY_R:
            self._logger.info(f"watcher got primary clip event: {clip}")
            self._saved_clip = clip
        if clip and key == glfw.KEY_Q:
            self._logger.info(f"watcher got secondary clip event: {clip}")
            self._secondary_clip = clip
        elif key:
            self._logger.info(f"watcher got key event: {key}")
            self._handle_key(key)
        else:
            self._logger.info(f"watcher got unknown event: {event}")

    def _open_search(self, url):
        if self._last_hover:
            search_term = self._last_hover.surface()
        elif last_sdata:
            search_term = self._last_sdata.original
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

    def _process(self):
        """Take a fresh screenshot and process it. if relevant, trigger drawing and update watch"""

        if self._secondary_clip:
            path = take_screenshot_clip_only(
                self._options.NotesFolder, self._secondary_clip
            )
            sdata = process_image_light(path, self._options, self._recognizer)
            if sdata:
                self._logger.debug("secondary clip: %s", sdata.original)
        self._secondary_clip = None

        (full_path, text_path) = take_screenshots(
            self._options.NotesFolder, self._saved_clip
        )
        sdata = process_image(self._options, self._recognizer, full_path, text_path)
        if sdata:
            self._last_sdata = sdata
            self._update_watch()
            self._overlay.draw(
                lambda c: draw(c, self._options, self._saved_clip, sdata)
            )  # TODO: draw secondary data, if present

    def _update_hover(self):
        """Check if the mouse cursor is hovering over a token, and if so save the token"""
        if self._saved_clip and self._last_sdata:
            hover = self._find_hover(self._saved_clip, self._last_sdata.tokens)
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

    def _load_clips(self):
        clips = load_json(self._clips_path)
        if clips and len(clips) > 0:
            clip = clips[0]
            self._saved_clip = skia.Rect.MakeXYWH(
                clip["x"], clip["y"], clip["w"], clip["h"]
            )

    def _save_clips(self):
        clip = {
            "x": self._saved_clip.x(),
            "y": self._saved_clip.y(),
            "w": self._saved_clip.width(),
            "h": self._saved_clip.height(),
        }
        clips = [clip]
        save_json(self._clips_path, clips)

    def run(self):
        """Primary watch loop, periodically takes screenshots and reprocesses text"""

        self._load_clips()

        while not self._stop_flag.is_set():
            try:
                event = self._event_queue.get(timeout=0.5)
            except queue.Empty:
                event = None
            self._handle_event(event)
            changed = self._has_screen_changed()
            if self._saved_clip and (not self._watch_paths or changed or event):
                self._overlay.clear(block=True)
                try:
                    self._process()
                except Exception as e:
                    self._logger.error(
                        "Exception while processing screenshot; %s", e.message
                    )
                    self.stop()
                    self._overlay.stop()
            self._update_hover()

        self._save_clips()

    def _get_first_non_punct(self, sdata):
        first_line = sdata.cdata[0]
        for cdata in first_line:
            if not is_punctuation(cdata.text):
                return cdata
        return None

    def _get_watch_regions(self, sdata):
        watches = []

        blocks = sdata.raw_data.blocks
        # find largest block
        block = max(blocks, key=lambda block: block.width * block.height)
        # find middle char in block
        line = block.lines[trunc(len(block.lines) / 2)]
        middle = line[trunc(len(line) / 2)]
        watches.append(middle)

        first = self._get_first_non_punct(sdata)
        if first is None:
            first = sdata.cdata[0][0]
            self._logger.warn(
                "failed to find non punctuation, using first character for watch: %s",
                first,
            )
        watches.append(first)

        regions = []
        for watch in watches:
            x = self._saved_clip.x() + watch.left + self._WATCH_MARGIN
            y = self._saved_clip.y() + watch.top + self._WATCH_MARGIN
            w = watch.width - self._WATCH_MARGIN * 2
            if w <= 0:
                w = watch.width
            h = watch.height - self._WATCH_MARGIN * 2
            if h <= 0:
                h = watch.height

            if w > 0 and h > 0:
                region = (x, y, w, h)
                regions.append(region)
                self._logger.debug("watch char: %s, region: %s", watch.text, region)

        return regions

    def _update_watch(self):
        new_watch_regions = self._get_watch_regions(self._last_sdata)
        if len(new_watch_regions) > 0:
            self._watch_regions = new_watch_regions
            self._watch_paths = take_watch_screenshot(
                self._options.NotesFolder, self._watch_regions
            )
        else:
            self._logger.warn("failed to find watch regions")

    def _has_screen_changed(self):
        if self._options.no_watch:
            return False
        if not self._watch_regions or not self._watch_paths:
            return False
        return screen_changed(
            self._options.NotesFolder, self._watch_paths, self._watch_regions
        )
