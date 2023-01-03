import os

from zoritori.files import get_path
from zoritori.strings import is_ascii


def _filter_seen_vocab(folder, new_words):
    path = get_path(folder, "vocabulary", "txt")
    with open(path, "a+", encoding="utf-8") as file:
        file.seek(0)
        lines = file.read().split("\n")
        old_words = set(lines)
        new_words = [word for word in set(new_words) if word not in old_words]
        for word in new_words:
            file.write(word)
            file.write("\n")
        return new_words


def _is_vocab(token):
    # filter out punctuation, particles, ascii:
    part_of_speech = token.part_of_speech()[0]
    return (
        part_of_speech != "補助記号"
        and part_of_speech != "助詞"
        and not is_ascii(token.surface())
    )


def save_vocabulary(folder, tokens, img_path=None):
    path = get_path(folder, "vocabulary", "md", dated=False)
    words = [t.dictionary_form() for t in tokens if _is_vocab(t)]
    words = _filter_seen_vocab(folder, words)
    if len(words) == 0:
        return False
    with open(path, "a", encoding="utf-8") as file:
        if img_path:
            img_file = os.path.basename(img_path)
            file.write(f"![]({img_file})\n")
        for word in words:
            file.write(word)
            file.write("\n")
        return True
