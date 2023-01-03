import skia
import pyautogui

from zoritori.files import load_json, save_json
from zoritori.types import Box, Root, Token


def is_mouse_inside(box: Box):
    rect = skia.Rect.MakeXYWH(box.screenx, box.screeny, box.width, box.height)
    pos = pyautogui.position()
    pixel = skia.Rect.MakeXYWH(pos.x, pos.y, 1, 1)
    return rect.intersect(pixel)


def find_hover(tokens: list[Token]):
    for t in tokens:
        if is_mouse_inside(t.box()):
            return t
    return None


def load_clips(path):
    clips = load_json(path)
    if clips and len(clips) > 0:
        clip = clips[0]
        context = Root(
            clip["screenx"], clip["screeny"], clip["clientx"], clip["clienty"]
        )
        return Box(clip["x"], clip["y"], clip["w"], clip["h"], context)
    return None


def save_clips(clip, path):
    if not clip:
        return
    clip = {
        "x": clip.x,
        "y": clip.y,
        "screenx": clip.screenx - clip.x,
        "screeny": clip.screeny - clip.y,
        "clientx": clip.clientx - clip.x,
        "clienty": clip.clienty - clip.y,
        "w": clip.width,
        "h": clip.height,
    }
    clips = [clip]
    save_json(path, clips)