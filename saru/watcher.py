import logging
import os
import threading
import queue
import time
import webbrowser
from pathlib import Path
from math import trunc
from dataclasses import dataclass

import glfw
import skia

from saru.overlay import Overlay
from saru.drawing import draw
from saru.screenshots import (
    take_screenshots,
    take_watch_screenshot,
    take_fullscreen_screenshot,
    screen_changed,
    take_screenshot_clip_only,
)
from saru.saru import process_image, process_image_light
from saru.vocabulary import save_vocabulary
from saru.strings import is_punctuation
from saru.files import load_json, save_json
from saru.types import SaruData
from saru.clips import save_clips, load_clips, find_hover
import saru.dictionary as dictionary


@dataclass
class RenderState:
    """Snapshot of app state that gets drawn to the screen"""

    fullscreen: bool
    translate: bool
    debug: bool
    parts_of_speech: bool
    subtitle_size: int
    subtitle_margin: int
    furigana_size: int
    primary_data: SaruData
    primary_clip: skia.Rect
    secondary_data: list[str]
    secondary_clip: skia.Rect


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
        elif self._last_sdata:
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
            case glfw.KEY_MINUS:
                self._options.FuriganaSize = self._options.FuriganaSize - 1
            case glfw.KEY_EQUAL:
                self._options.FuriganaSize = self._options.FuriganaSize + 1
            case _:
                pass

    def _process(self):
        """Take a fresh screenshot and process it. if relevant, trigger drawing and update watch"""

        render_state = RenderState(
            self._options.fullscreen,
            self._options.translate,
            self._options.debug,
            self._options.parts_of_speech,
            self._options.SubtitleSize,
            self._options.SubtitleMargin,
            self._options.FuriganaSize,
            None,
            None,
            None,
            None,
        )
        if self._secondary_clip:
            path = take_screenshot_clip_only(
                self._options.NotesFolder, self._secondary_clip
            )
            sdata = process_image_light(path, self._options, self._recognizer)
            if sdata and len(sdata.original) > 0:
                self._logger.debug("secondary clip: %s", sdata.original)
                render_state.secondary_data = dictionary.lookup(sdata.original)
                render_state.secondary_clip = self._secondary_clip
            self._secondary_clip = None

        if self._saved_clip:  # TODO: could check if this has changed
            (full_path, text_path) = take_screenshots(
                self._options.NotesFolder, self._saved_clip
            )
            x = self._saved_clip.x()
            y = self._saved_clip.y()
            sdata = process_image(
                self._options, self._recognizer, full_path, text_path, x, y
            )
            if sdata:
                self._last_sdata = sdata
                self._update_watch()
                render_state.primary_clip = self._saved_clip
                render_state.primary_data = sdata
                self._overlay.draw(lambda c: draw(c, render_state))
        elif self._options.fullscreen:
            full_path = take_fullscreen_screenshot(self._options.NotesFolder)
            sdata = process_image(self._options, self._recognizer, full_path, None)
            if sdata:
                self._last_sdata = sdata
                self._update_watch()
                b = sdata.raw_data.get_primary_block()
                rect = skia.Rect.MakeXYWH(b.box.x, b.box.y, b.box.width, b.box.height)
                render_state.primary_clip = rect
                render_state.primary_data = sdata
                self._overlay.draw(lambda c: draw(c, render_state))

    def _update_hover(self):
        """Check if the mouse cursor is hovering over a token, and if so save the token"""
        if self._saved_clip and self._last_sdata:
            hover = find_hover(self._saved_clip, self._last_sdata.tokens)
            if hover != self._last_hover:
                self._last_hover = hover
                self._logger.info(
                    f"hovered token: {hover.surface() if hover else None}"
                )
                if hover:
                    dictionary.debug(hover.surface())

    def _any_clip(self):
        return self._saved_clip or self._secondary_clip or self._options.fullscreen

    def run(self):
        """Primary watch loop, periodically takes screenshots and reprocesses text"""

        self._saved_clip = load_clips(self._clips_path)

        while not self._stop_flag.is_set():
            try:
                event = self._event_queue.get(timeout=0.5)
            except queue.Empty:
                event = None
            self._handle_event(event)
            changed = self._has_screen_changed()
            if self._any_clip() and (not self._watch_paths or changed or event):
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

        save_clips(self._saved_clip, self._clips_path)

    def _get_first_non_punct(self, sdata):
        first_line = sdata.cdata[0]
        for cdata in first_line:
            if not is_punctuation(cdata.text):
                return cdata
        return None

    def _get_watch_regions(self, sdata):
        watches = []

        blocks = sdata.raw_data.blocks
        if len(blocks) < 1:
            self._logger.debug("raw data has no blocks")
            return []

        # find largest block
        block = sdata.raw_data.get_primary_block()

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
            x = watch.left + self._WATCH_MARGIN
            y = watch.top + self._WATCH_MARGIN
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
            else:
                self._logger.debug("failed to find watches > 0")

        return regions

    def _update_watch(self):
        new_watch_regions = self._get_watch_regions(self._last_sdata)
        if len(new_watch_regions) > 0:
            self._watch_regions = new_watch_regions
        else:
            self._logger.warn("failed to find watch regions, using whole clip")
            x = self._saved_clip.x()
            y = self._saved_clip.y()
            w = self._saved_clip.width()
            h = self._saved_clip.height()
            self._watch_regions = [(x, y, w, h)]
        self._watch_paths = take_watch_screenshot(
            self._options.NotesFolder, self._watch_regions
        )

    def _has_screen_changed(self):
        if self._options.no_watch:
            return False
        if not self._watch_regions or not self._watch_paths:
            return False
        return screen_changed(
            self._options.NotesFolder, self._watch_paths, self._watch_regions
        )
