import logging



_logger = logging.getLogger("zoritori")


def _entry_to_list(entry):
    result = []
    if entry.kanji_forms and len(entry.kanji_forms) > 0:
        result.append(entry.kanji_forms[0].text)
    if entry.kana_forms and len(entry.kana_forms) > 0:
        result.append(entry.kana_forms[0].text)
    if entry.senses and len(entry.senses) > 0:
        result.append(entry.senses[0].text())
    return result


def lookup(s):
    return None
