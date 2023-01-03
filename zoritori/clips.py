import skia
import pyautogui

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
