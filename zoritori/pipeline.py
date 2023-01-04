import logging
import sys
import os
from pathlib import Path
from operator import itemgetter
from statistics import median
from dataclasses import dataclass

from zoritori.translator import translate
from zoritori.tokenizer import tokenize
from zoritori.types import Furigana, ZoritoriData, Box
from zoritori.vocabulary import save_vocabulary


_logger = logging.getLogger("zoritori")


def _percent_ascii(ldata):
    a = 0
    t = 0
    for line in ldata:
        for d in line:
            t += 1
            if ord(d.text) < 128:
                a += 1
    return a / t * 100


def _is_junk(ldata):
    if len(ldata) == 0:
        return True
    conf = median([d.conf for line in ldata for d in line])
    return conf < 75 or _percent_ascii(ldata) > 25


def _get_text(ldata):
    lines = ["".join([d.text for d in line]) for line in ldata]
    return "\n".join(lines)


def _recognize_tokenize_translate(options, recognizer, filename, context):
    debug = options.debug
    should_translate = options.Translate

    _logger.debug("recognizing...")
    raw_data = recognizer.recognize(filename, context)
    ldata = raw_data.get_lines()
    text = _get_text(ldata)

    # if _is_junk(ldata):
    #     _logger.debug("got junk: %s", text)
    #     return None

    _logger.debug("tokenizing...")
    tokens = tokenize(text, ldata)

    translation = None
    if should_translate:
        _logger.debug("translating...")
        translation = translate(text, options.DeepLUrl, options.DeepLKey)

    return ZoritoriData(text, translation, ldata, tokens, raw_data)


def log_debug(zoritori):
    #    for line in zoritori["cdata"]:
    #        for d in line:
    #            _logger.debug("%s %s %s", d.text, d.line_num, d.conf)
    _logger.info(zoritori.original)
    if zoritori.translation:
        _logger.info(zoritori.translation)


def process_image_light(path, options, recognizer):
    zoritori = _recognize_tokenize_translate(options, recognizer, path)
    if zoritori and options.debug:
        log_debug(zoritori)
    return zoritori


def process_image(options, recognizer, full_path, text_path, context):
    """Processes an image for vocabulary collection and saving screenshots"""
    zoritori = _recognize_tokenize_translate(
        options, recognizer, text_path or full_path, context
    )
    if zoritori is None:
        return None
    notes_dir = options.NotesFolder
    if notes_dir:
        text = zoritori.original
        cleaned_up = text
        for c in ["<", ">", ":", '"', "/", "\\", "|", "?", "*", "\n"]:
            cleaned_up = cleaned_up.replace(c, "-")
            new_filename = (Path(full_path).name).replace("xxxxx", cleaned_up)
        notes_pic = Path(notes_dir) / new_filename
        os.rename(full_path, notes_pic)
        if not save_vocabulary(notes_dir, zoritori.tokens, notes_pic):
            os.remove(notes_pic)
    if options.debug:
        log_debug(zoritori)
    return zoritori
