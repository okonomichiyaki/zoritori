import pyautogui
import skia

from saru.files import get_path
from saru.types import CharacterData


def take_watch_screenshot(folder: str, region):
    watch_path = get_path(folder, "screenshot", "png", title="watch")
    pyautogui.screenshot(watch_path, region=region)
    return watch_path


def take_screenshots(folder: str, clip: skia.Rect):
    full_path = get_path(folder, "screenshot", "png", title="xxxxx", dated=True, timed=True)
    pyautogui.screenshot(full_path)

#    watch_path = get_path(folder, "screenshot", "png", title="watch")
#    h = clip.height() / 9
#    watch_clip = (clip.x(), clip.y() + h, clip.width(), h)
#    pyautogui.screenshot(watch_path, region=watch_clip)

    clip_path = get_path(folder, "screenshot", "png", title="text")
    pyautogui.screenshot(clip_path, region=(clip.x(), clip.y(), clip.width(), clip.height()))

    return (full_path, clip_path)

# returns (left, top, width, height) or None
def locate(path):
    try:
        return pyautogui.locateOnScreen(path, confidence=0.9, grayscale=True)
    except pyautogui.ImageNotFoundException:
        return None


def screen_changed(folder, path, region):
    path2 = get_path(folder, "screenshot", "png", title="watch2")
    pyautogui.screenshot(path2, region=region)
    try:
        return not pyautogui.locate(path, path2, grayscale=False)
    except pyautogui.ImageNotFoundException:
        return True
