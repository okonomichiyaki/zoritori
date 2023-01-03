import logging
import platform

if platform.system() == "Windows":
    from jisho_api.word import Word
else:
    from jamdict import Jamdict


_logger = logging.getLogger("zoritori")


def _jamdict_entry_to_list(entry):
    result = []
    if entry.kanji_forms and len(entry.kanji_forms) > 0:
        result.append(entry.kanji_forms[0].text)
    if entry.kana_forms and len(entry.kana_forms) > 0:
        result.append(entry.kana_forms[0].text)
    if entry.senses and len(entry.senses) > 0:
        result.append(entry.senses[0].text())
    return result


def lookup(s):
    if platform.system() == "Windows":
        r = Word.request(s)
        if r and len(r.data) > 0:
            c = r.data[0]
            j = c.japanese[0]
            s = c.senses[0]
            ed = s.english_definitions[0] if len(s.english_definitions) > 0 else None
            return [j.word, j.reading, ed]
        else:
            return None
    else:
        jam = Jamdict()
        result = jam.lookup(s)
        if result and len(result.entries) > 0:
            entry = result.entries[0]
            return _entry_to_list(entry)
        else:
            return None
