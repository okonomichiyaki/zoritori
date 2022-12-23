import logging
from dataclasses import dataclass

import sudachipy
import skia

from saru.strings import katakana_to_hiragana, all_kana, is_ascii


_logger = logging.getLogger("saru")


@dataclass
class Furigana:
    reading: str
    x: int
    y: int


@dataclass
class Box:
    """Generic bounding box"""

    left: int
    top: int
    width: int
    height: int

    @property
    def x(self):
        return self.left

    @property
    def y(self):
        return self.top


@dataclass
class CharacterData:
    """OCR data for a single character"""

    text: str
    line_num: int
    conf: float
    box: Box

    @property
    def x(self):
        return self.box.left

    @property
    def y(self):
        return self.box.top

    @property
    def left(self):
        return self.box.left

    @property
    def top(self):
        return self.box.top

    @property
    def width(self):
        return self.box.width

    @property
    def height(self):
        return self.box.height


@dataclass
class BlockData:
    """OCR data for a block of text"""

    lines: list[list[CharacterData]]
    box: Box

    @property
    def x(self):
        return self.box.left

    @property
    def y(self):
        return self.box.top

    @property
    def left(self):
        return self.box.left

    @property
    def top(self):
        return self.box.top

    @property
    def width(self):
        return self.box.width

    @property
    def height(self):
        return self.box.height


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
        return skia.Rect.MakeXYWH(left, top, width, height)

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


@dataclass
class RawData:
    """Response data from OCR engine"""

    lines: list[list[CharacterData]]
    blocks: list[BlockData]

    def lines(self):
        return self.lines

    def blocks(self):
        return self.blocks


@dataclass
class SaruData:
    """Enriched data from tokenization, translation, etc."""

    original: str
    translation: str
    cdata: list[list[CharacterData]]
    tokens: list[Token]
    furigana: list[Furigana]
    raw_data: RawData
