import platform


def get_ja_font():  # TODO: magic strings
    if platform.system() == "Windows":
        # "ms gothic"
        return "meiryo"
    if platform.system() == "Darwin":
        return "Hiragino Sans"
    else:
        return "Noto Sans CJK JP"
