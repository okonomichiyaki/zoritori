from itertools import groupby

import pytest

import saru.tokenizer as t

# texts taken from `samples/examples of numerals.png`

lines = [
    "戦闘不能となるのは退却したとき、",
    "兵士数がOになったとき、",
    "士気がOになったときだ"
]

def test_tokenize():
    text = lines[0]
    tokens = t.tokenize(text)
    assert tokens[0].surface() == "戦闘"
    assert tokens[0].has_kanji()
    assert tokens[2].surface() == "と"
    assert not tokens[2].has_kanji()

def test_tokenize_numeral_not_kanji():
    text = lines[1]
    tokens = t.tokenize(text)
    assert tokens[3].surface() == "O"
    # OCR sees letter O instead of number 0, but either way not kanji
    # assert tokens[3]["part_of_speech"][1] == "数詞"
    assert not tokens[3].has_kanji()

def test_tokenize_multi_line():
    text = "\n".join(lines)
    tokens = t.tokenize(text)
    tokens_by_lines = [list(it) for k, it in groupby(tokens, lambda token: token.line_num())]
    assert len(tokens_by_lines) == 3

def test_merge_bug():
    text = "まず、わしの軍団"
    tokens = t.tokenize(text)
    assert tokens[-1].surface() == "軍団"
    assert tokens[-1].has_kanji()
