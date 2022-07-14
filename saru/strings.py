

def is_ascii(s):
    """Returns true if string is all ASCII"""
    try:
        s.encode('ascii')
    except UnicodeEncodeError:
        return False
    else:
        return True


def katakana_to_hiragana(s):
    """Converts katakana characters in the string to hiragana"""
    lower = ord("゠")
    upper = ord("ヿ")
    diff = ord("ア") - ord("あ")

    def convert(c):
        point = ord(c)
        if point >= lower and point <= upper:
            return chr(point - diff)
        else:
            return c

    return "".join(map(convert, s))


def all_kana(s):
    """Returns true if the string is all hiragana or katakana"""
    hlower = ord('\u3041')
    hupper = ord('\u3096')
    klower = ord('\u30A0')
    kupper = ord('\u30FF')

    def is_kana(c):
        point = ord(c)
        return point < hupper and point > hlower or point < kupper and point > klower

    return all(is_kana(c) for c in s)
