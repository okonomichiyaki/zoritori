import logging
from dataclasses import dataclass

import sudachipy
import skia

from saru.strings import katakana_to_hiragana, all_kana, is_ascii


_logger = logging.getLogger("saru")


@dataclass
class Furigana:
    reading: str
    x: int  # TODO why does this class has its own coords
    y: int


@dataclass
class Root:
    """Origin parent context for boxes"""

    screenx: int
    screeny: int
    clientx: int
    clienty: int


class Box:
    """Generic rectangular box"""

    def __init__(self, left, top, width, height, parent_context=None):
        self._left = left
        self._top = top
        self._width = width
        self._height = height
        self._parent_context = parent_context

    def to_skia_rect(self):
        return skia.Rect.MakeXYWH(self.clientx, self.clienty, self.width, self.height)

    @property
    def screenx(self):
        if self._parent_context:
            return self._parent_context.screenx + self._left
        else:
            return self._left

    @property
    def screeny(self):
        if self._parent_context:
            return self._parent_context.screeny + self._top
        else:
            return self._top

    @property
    def clientx(self):
        if self._parent_context:
            return self._parent_context.clientx + self._left
        else:
            return self._left

    @property
    def clienty(self):
        if self._parent_context:
            return self._parent_context.clienty + self._top
        else:
            return self._top

    @property
    def x(self):
        return self._left

    @property
    def y(self):
        return self._top

    @property
    def left(self):
        return self._left

    @property
    def top(self):
        return self._top

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height


@dataclass
class CharacterData:
    """OCR data for a single character"""

    text: str
    line_num: int
    conf: float
    box: Box

    def __getattr__(self, name):
        box_methods = [f for f in dir(Box) if not f.startswith("_")]
        if name in box_methods:
            return getattr(self.box, name)
        else:
            raise AttributeError


@dataclass
class BlockData:
    """OCR data for a block of text"""

    lines: list[list[CharacterData]]
    box: Box

    def char_count(self):
        return sum(map(lambda line: len(line), self.lines))

    def __getattr__(self, name):
        box_methods = [f for f in dir(Box) if not f.startswith("_")]
        if name in box_methods:
            return getattr(self.box, name)
        else:
            raise AttributeError


class MergedName:
    """Wrapper around two Sudachi Morphemes, representing a full name"""

    def __init__(self, first, second):
        self._first = first
        self._second = second

    def begin(self):
        return self._first.begin()

    def end(self):
        return self._second.end()

    def surface(self):
        return self._first.surface() + self._second.surface()

    def dictionary_form(self):
        return self.surface()

    def reading_form(self):
        return self._first.reading_form() + self._second.reading_form()

    def part_of_speech(self):
        return ("名詞", "固有名詞", "人名", "姓名", "*", "*")


class Token:
    """Wrapper around a Sudachi Morpheme, providing some utilities"""

    def __init__(self, sudachi_morpheme, line_num, char_num, cdata):
        self._morpheme = sudachi_morpheme
        self._line_num = line_num
        self._char_num = char_num
        self._cdata = cdata
        self._sudachi_methods = [
            f for f in dir(sudachipy.Morpheme) if not f.startswith("_")
        ]

    def box(self):
        left = self._cdata[0].left
        top = self._cdata[0].top
        height = self._cdata[0].height
        width = self._cdata[-1].left + self._cdata[-1].width - left
        return skia.Rect.MakeXYWH(left, top, width, height)  # ??? coordinates

    def line_num(self):
        return self._line_num

    def char_num(self):
        return self._char_num

    def length(self):
        return self._morpheme.end() - self._morpheme.begin()

    def __getattr__(self, name):
        if name in self._sudachi_methods:
            return getattr(self._morpheme, name)
        else:
            raise AttributeError

    def __repr__(self):
        return f"saru.Token<{self._morpheme.surface()}>"

    def length(self):
        return self._morpheme.end() - self._morpheme.begin()

    def part_of_speech(self, index=None):
        if index:
            return self._morpheme.part_of_speech()[index]
        else:
            return self._morpheme.part_of_speech()

    def reading_form(self):
        return katakana_to_hiragana(self._morpheme.reading_form())

    def has_kanji(self):
        if self._morpheme.part_of_speech()[1] == "数詞":
            return False
        if self._morpheme.part_of_speech()[0] == "補助記号":
            return False
        if self._morpheme.part_of_speech()[0] == "空白":
            return False
        if is_ascii(self._morpheme.surface()):
            return False
        if all_kana(self._morpheme.surface()):
            return False
        return True


class RawData:
    """Response data from OCR engine"""

    def __init__(self, lines, blocks):
        self.lines = lines
        self.blocks = blocks
        self._primary_block = None

    def _find_primary_block(self):
        if self._primary_block:
            return
        if len(self.blocks) < 1:
            return
        screen_height = 1080  # TODO: magic number
        screen_width = 1920  # TODO: magic number
        blocks = filter(lambda block: block.screeny > screen_height / 2, self.blocks)
        # largest_by_pixels = max(self.blocks, key=lambda block: block.width * block.height)
        # largest_by_chars = max(self.blocks, key=lambda block: block.char_count())
        closest_to_center = min(
            blocks,
            key=lambda block: abs(block.screenx + block.width / 2 - screen_width / 2),
        )
        self._primary_block = closest_to_center

    def get_primary_block(self):
        self._find_primary_block()
        return self._primary_block

    def get_lines(self):
        self._find_primary_block()
        if self._primary_block:
            return self._primary_block.lines
        else:
            return self.lines


@dataclass
class SaruData:
    """Enriched data from tokenization, translation, etc."""

    original: str
    translation: str
    cdata: list[list[CharacterData]]
    tokens: list[Token]
    furigana: list[Furigana]
    raw_data: RawData
