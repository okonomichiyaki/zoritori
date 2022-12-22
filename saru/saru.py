import logging
import sys
import os
from operator import itemgetter
from statistics import median
from dataclasses import dataclass

from saru.translator import translate
from saru.tokenizer import tokenize
from saru.types import Furigana
from saru.vocabulary import save_vocabulary


_logger = logging.getLogger("saru")


def _get_furigana(tokens, cdata, level):
    if level == "none":
        return []

    def furigana(token):
        line_num = token.line_num()
        char_num = token.char_num()
        length = token.length()
        reading = token.reading_form()
        first = cdata[line_num][char_num]
        last = cdata[line_num][char_num + length - 1]
        left = first.left
        right = last.left + last.width
        x = left + (right - left) / 2
        y = first.top
        return Furigana(reading, x, y)

    def filter(m):
        if level == "all":
            return m.has_kanji()
        if level == "some":
            return m.part_of_speech()[1] == "固有名詞"
        else:
            return False

    return [furigana(token) for token in tokens if filter(token)]


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


def _recognize_tokenize_translate(options, recognizer, filename):
    debug = options.debug
    should_translate = options.translate
    furigana_level = options.furigana

    raw_data = recognizer.recognize(filename)
    ldata = raw_data.lines
    text = _get_text(ldata)

    #    if _is_junk(ldata):
    #        _logger.debug("got junk: %s", text)
    #        return None

    tokens = tokenize(text, ldata)
    furigana = _get_furigana(tokens, ldata, furigana_level)

    translation = None
    if should_translate:
        translation = translate(text, options.DeepLUrl, options.DeepLKey)

    return {
        "original": text,
        "translation": translation,
        "cdata": ldata,
        "tokens": tokens,
        "furigana": furigana,
        "raw_data": raw_data,
    }


def log_debug(saru):
    #    for line in saru["cdata"]:
    #        for d in line:
    #            _logger.debug("%s %s %s", d.text, d.line_num, d.conf)
    _logger.info(saru["original"])
    if saru["translation"]:
        _logger.info(saru["translation"])


def process_image_light(options, recognizer):
    saru = _recognize_tokenize_translate(options, recognizer, options.filename)
    if saru and options.debug:
        log_debug(saru)


def process_image(options, recognizer, full_path, text_path):
    """Processes an image for vocabulary collection and saving screenshots"""
    saru = _recognize_tokenize_translate(options, recognizer, text_path)
    if saru is None:
        os.remove(text_path)
        os.remove(full_path)
        return None
    text = saru["original"]
    os.remove(text_path)
    cleaned_up = text
    for c in ["<", ">", ":", '"', "/", "\\", "|", "?", "*", "\n"]:
        cleaned_up = cleaned_up.replace(c, "-")
    #    new_path = full_path.replace("xxxxx", cleaned_up)
    #    os.rename(full_path, new_path)
    #    if not save_vocabulary(options.NotesFolder, saru["tokens"], new_path):
    #        os.remove(new_path)
    if options.debug:
        log_debug(saru)
    return saru
