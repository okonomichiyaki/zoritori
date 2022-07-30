import pytest

import saru.strings as s


def test_is_ascii():
    assert s.is_ascii("abc")


def test_is_not_ascii():
    assert not s.is_ascii("あかさ")


def test_katakana_to_hiragana_converts():
    assert s.katakana_to_hiragana("アカサ") == "あかさ"


def test_katakana_to_hiragana_no_op():
    assert s.katakana_to_hiragana("あかさ") == "あかさ"


def test_all_kana():
    assert s.all_kana("あかさ")


def test_not_all_kana():
    assert not s.all_kana("赤")
