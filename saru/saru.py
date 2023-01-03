import logging
import sys
import os
from pathlib import Path
from operator import itemgetter
from statistics import median
from dataclasses import dataclass

from saru.translator import translate
from saru.tokenizer import tokenize
from saru.types import Furigana, SaruData, Box
from saru.vocabulary import save_vocabulary


_logger = logging.getLogger("saru")


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
    should_translate = options.translate

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

    return SaruData(text, translation, ldata, tokens, raw_data)


def log_debug(saru):
    #    for line in saru["cdata"]:
    #        for d in line:
    #            _logger.debug("%s %s %s", d.text, d.line_num, d.conf)
    _logger.info(saru.original)
    if saru.translation:
        _logger.info(saru.translation)


def process_image_light(path, options, recognizer):
    saru = _recognize_tokenize_translate(options, recognizer, path)
    if saru and options.debug:
        log_debug(saru)
    return saru


def process_image(options, recognizer, full_path, text_path, context):
    """Processes an image for vocabulary collection and saving screenshots"""
    saru = _recognize_tokenize_translate(
        options, recognizer, text_path or full_path, context
    )
    if saru is None:
        return None
    notes_dir = options.NotesFolder
    if options.NotesFolder and len(options.NotesFolder) > 0:
        text = saru.original
        cleaned_up = text
        for c in ["<", ">", ":", '"', "/", "\\", "|", "?", "*", "\n"]:
            cleaned_up = cleaned_up.replace(c, "-")
            new_filename = (Path(full_path).name).replace("xxxxx", cleaned_up)
        notes_path = Path(notes_dir) / new_filename
        os.rename(full_path, notes_path)
        if not save_vocabulary(options.NotesFolder, saru.tokens, notes_path):
            os.remove(notes_path)
    if options.debug:
        log_debug(saru)
    return saru
