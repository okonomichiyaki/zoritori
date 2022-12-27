import skia
import pyautogui

from saru.files import load_json, save_json


def is_mouse_inside(clip, rect):
    shifted = skia.Rect.MakeXYWH(
        clip.x() + rect.x(), clip.y() + rect.y(), rect.width(), rect.height()
    )
    pos = pyautogui.position()
    pixel = skia.Rect.MakeXYWH(pos.x, pos.y, 1, 1)
    return shifted.intersect(pixel)


def find_hover(clip, tokens):
    for t in tokens:
        if is_mouse_inside(clip, t.box()):
            return t
    return None


def load_clips(path):
    clips = load_json(path)
    if clips and len(clips) > 0:
        clip = clips[0]
        return skia.Rect.MakeXYWH(clip["x"], clip["y"], clip["w"], clip["h"])
    return None


def save_clips(clip, path):
    if not clip:
        return
    clip = {
        "x": clip.x(),
        "y": clip.y(),
        "w": clip.width(),
        "h": clip.height(),
    }
    clips = [clip]
    save_json(path, clips)
