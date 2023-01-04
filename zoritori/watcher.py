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

from zoritori.overlay import Overlay
from zoritori.drawing import draw
from zoritori.screenshots import (
    take_screenshots,
    take_watch_screenshot,
    screen_changed,
    take_screenshot_clip_only,
)
from zoritori.pipeline import process_image, process_image_light
from zoritori.vocabulary import save_vocabulary
from zoritori.strings import is_punctuation
from zoritori.files import load_json, save_json
from zoritori.types import ZoritoriData, Box, Token
from zoritori.settings import save_clips, load_clips
import zoritori.dictionary as dictionary


@dataclass
class RenderState:
    """Snapshot of app state that gets drawn to the screen"""

    translate: bool
    debug: bool
    parts_of_speech: bool
    furigana: str
    subtitle_size: int
    subtitle_margin: int
    furigana_size: int
    primary_data: ZoritoriData
    primary_clip: Box
    secondary_data: list[str]
    secondary_clip: Box
    hover: Token
    hover_lookup: list[str]


class Watcher(threading.Thread):
    def __init__(self, options, recognizer, event_queue, overlay, watch_dir, settings_path):
        threading.Thread.__init__(self)
        self._stop_flag = threading.Event()
        self._WATCH_MARGIN = 5  # TODO: magic number
        self._logger = logging.getLogger("zoritori")

        self._options = options
        self._recognizer = recognizer
        self._event_queue = event_queue
        self._overlay = overlay

        self._watch_paths = None
        self._watch_dir = watch_dir
        self._watch_regions = None
        self._last_sdata = None
        self._last_hover = None
        self._last_hover_lookup = None
        self._saved_clip = None
        self._saved_clip_dirty = True
        self._secondary_clip = None
        self._settings_path = settings_path
        self._render_state = None

    def stop(self):
        self._stop_flag.set()

    def _handle_event(self, event):
        """Handles input events from the overlay"""
        if not event:
            return False
        clip = event.get_clip()
        key = event.get_key()
        if clip and (key == glfw.KEY_R or key == glfw.MOUSE_BUTTON_1):
            self._logger.debug(f"watcher got primary clip event: {clip}")
            self._saved_clip = clip
            self._saved_clip_dirty = True
            return True
        if clip and (key == glfw.KEY_Q or key == glfw.MOUSE_BUTTON_2):
            self._logger.debug(f"watcher got secondary clip event: {clip}")
            self._secondary_clip = clip
            self._saved_clip_dirty = False
            return True
        elif key:
            self._logger.debug(f"watcher got key event: {key}")
            return self._handle_key(key)
        else:
            self._logger.debug(f"watcher got unknown event: {event}")
            return False

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
                return True
            case glfw.KEY_D:
                self._options.debug = not self._options.debug
                return True
            case glfw.KEY_T:
                self._options.Translate = not self._options.Translate
                return True
            case glfw.KEY_J:
                self._open_search("http://jisho.org/search/")
                return False
            case glfw.KEY_W:
                self._open_search("https://ja.wikipedia.org/wiki/")
                return False
            case glfw.KEY_E:
                self._open_search("https://en.wikipedia.org/w/index.php?search=")
                return False
            case glfw.KEY_MINUS:
                self._options.FuriganaSize = self._options.FuriganaSize - 1
                return True
            case glfw.KEY_EQUAL:
                self._options.FuriganaSize = self._options.FuriganaSize + 1
                return True
            case _:
                return False

    def _process(self):
        """Take a fresh screenshot and process it. if relevant, trigger drawing and update watch"""

        self._render_state = RenderState(
            self._options.Translate,
            self._options.debug,
            self._options.ProperNouns,
            self._options.Furigana,
            self._options.SubtitleSize,
            self._options.SubtitleMargin,
            self._options.FuriganaSize,
            None,
            None,
            None,
            None,
            None,
            None,
        )
        should_draw = False

        if self._secondary_clip:
            path = take_screenshot_clip_only(self._watch_dir, self._secondary_clip)
            sdata = process_image_light(path, self._options, self._recognizer, self._secondary_clip)
            if sdata and len(sdata.original) > 0:
                self._logger.debug("secondary clip: %s", sdata.original)
                self._render_state.secondary_data = dictionary.lookup(sdata.original)
                self._render_state.secondary_clip = self._secondary_clip
                self._render_state.primary_clip = self._saved_clip
                self._render_state.primary_data = self._last_sdata
                should_draw = True
            self._secondary_clip = None

        if self._saved_clip and self._saved_clip_dirty:
            (full_path, text_path) = take_screenshots(self._watch_dir, self._saved_clip)
            sdata = process_image(
                self._options,
                self._recognizer,
                full_path,
                text_path,
                self._saved_clip,
            )
            if sdata:
                self._last_sdata = sdata
                self._update_watch()
                self._render_state.primary_clip = self._saved_clip
                self._render_state.primary_data = sdata
                should_draw = True
        if should_draw:
            self._overlay.draw(lambda c: draw(c, self._render_state))


    def _update_hover(self):
        """Check if the mouse cursor is hovering over a token, and if so save the token"""
        if self._saved_clip and self._last_sdata:
            hover = self._find_hover(self._last_sdata.tokens)
            if hover != self._last_hover:
                self._last_hover = hover
                entry = dictionary.lookup(hover.surface()) if hover else None
                self._logger.debug(f"hovered token: %s", entry)
                self._last_hover_lookup = entry
                return True
        return False

    def _any_clip(self):
        return self._saved_clip or self._secondary_clip

    def run(self):
        """Primary watch loop, periodically takes screenshots and reprocesses text"""

        self._saved_clip = load_clips(self._settings_path)

        while not self._stop_flag.is_set():
            try:
                event = self._event_queue.get(timeout=0.5)
            except queue.Empty:
                event = None
            dirty = self._handle_event(event)
            changed = self._has_screen_changed()
            if self._any_clip() and (not self._watch_paths or changed or dirty):
                self._overlay.clear(block=True)
                try:
                    self._process()
                    self._update_hover()
                except Exception as e:
                    self._logger.error(
                        "Exception while processing screenshot; %s", e.message
                    )
                    self.stop()
                    self._overlay.stop()
            elif self._update_hover() and self._render_state:
                self._render_state.hover = self._last_hover
                self._render_state.hover_lookup = self._last_hover_lookup
                self._overlay.draw(lambda c: draw(c, self._render_state))

        save_clips(self._saved_clip, self._settings_path)

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
            x = watch.screenx + self._WATCH_MARGIN
            y = watch.screeny + self._WATCH_MARGIN
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
            x = self._saved_clip.screenx
            y = self._saved_clip.screeny
            w = self._saved_clip.width
            h = self._saved_clip.height
            self._watch_regions = [(x, y, w, h)]
        self._watch_paths = take_watch_screenshot(self._watch_dir, self._watch_regions)

    def _has_screen_changed(self):
        if self._options.no_watch:
            return False
        if not self._watch_regions or not self._watch_paths:
            return False
        return screen_changed(self._watch_dir, self._watch_paths, self._watch_regions)

    def _is_mouse_inside(self, box: Box):
        rect = skia.Rect.MakeXYWH(box.clientx, box.clienty, box.width, box.height)
        (x, y) = self._overlay.get_mouse_pos()
        pixel = skia.Rect.MakeXYWH(x, y, 1, 1)
        return rect.intersect(pixel)

    def _find_hover(self, tokens: list[Token]):
        for t in tokens:
            if self._is_mouse_inside(t.box()):
                return t
        return None
