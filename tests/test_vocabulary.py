from collections import Counter
import pytest

from zoritori.vocabulary import save_vocabulary
from zoritori.tokenizer import tokenize


def test_save_vocabulary(tmp_path):
    text = "戦闘不能となるのは退却したとき、兵士数が0になったとき、士気が0になったときだ"
    tokens = tokenize(text)
    result = save_vocabulary(str(tmp_path), tokens)
    assert result
    vocabtxt = tmp_path / "vocabulary.txt"
    with open(str(vocabtxt), encoding="utf-8") as file:
        output = file.read().split("\n")
    assert "戦闘" in output
    assert "、" not in output
    assert "0" not in output
    assert "の" not in output
    counter = Counter(output)
    assert 1 == counter["なる"]
    assert 1 == counter["とき"]
