import logging

from sudachipy import tokenizer, dictionary

from zoritori.types import Token, CharacterData, MergedName


_logger = logging.getLogger("zoritori")


def _convert(morphemes, ldata):
    line_num = 0
    char_count = 0
    prev_count = 0
    result = []
    for m in morphemes:
        if m.surface() == "\n":
            line_num += 1
            char_count += 1
            prev_count = char_count
            continue
        char_num = m.begin() - prev_count  # index of first char relative to the line
        length = m.end() - m.begin()
        cdata = ldata[line_num][char_num : char_num + length]
        if len(cdata) > 0:
            wrapped = Token(m, line_num, char_num, cdata)
            char_count += wrapped.length()
            result.append(wrapped)
    return result


def _merge_names(morphemes):
    def surname(m):
        return m.part_of_speech()[2] == "人名" and m.part_of_speech()[3] == "姓"

    def given_name(m):
        return m.part_of_speech()[2] == "人名" and m.part_of_speech()[3] == "名"

    if len(morphemes) < 2:
        return morphemes
    i = 0
    result = []
    while i < len(morphemes):
        m0 = morphemes[i]
        if i + 1 == len(morphemes):
            result.append(m0)
            break
        m1 = morphemes[i + 1]
        if surname(m0) and given_name(m1):
            result.append(MergedName(m0, m1))
            i += 2
        else:
            result.append(m0)
            i += 1
    return result


def tokenize(text: str, ldata: list[list[CharacterData]] = None) -> list[Token]:
    """Break text up into morphemes using Sudachi"""

    # for testing without OCR:
    if not ldata:
        lines = text.split("\n")
        ldata = [list(line) for line in lines]

    tokenizer_obj = dictionary.Dictionary().create()
    mode = tokenizer.Tokenizer.SplitMode.A
    morphemes = tokenizer_obj.tokenize(text, mode)
    for m in morphemes:
        part_of_speech = m.part_of_speech()[0]
        if part_of_speech == "空白":
            _logger.debug("\\n\t\t-\t\t%s", part_of_speech)
        else:
            _logger.debug(
                "%s\t%s\t%s\t%s",
                m.surface(),
                m.dictionary_form(),
                m.reading_form(),
                m.part_of_speech(),
            )
    morphemes = _merge_names(morphemes)
    return _convert(morphemes, ldata)
