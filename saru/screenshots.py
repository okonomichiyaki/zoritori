import logging
import pyautogui
import skia

from saru.files import get_path
from saru.types import CharacterData


_logger = logging.getLogger("saru")


def take_watch_screenshot(folder: str, regions):
    watch_paths = []
    for i, region in enumerate(regions):
        watch_path = get_path(folder, "screenshot", "png", title=f"watch_{i}_base")
        pyautogui.screenshot(watch_path, region=region)
        watch_paths.append(watch_path)
    return watch_paths


def take_screenshots(folder: str, clip: skia.Rect):
    full_path = get_path(
        folder, "screenshot", "png", title="xxxxx", dated=True, timed=True
    )
    pyautogui.screenshot(full_path)
    clip_path = get_path(folder, "screenshot", "png", title="text")
    pyautogui.screenshot(
        clip_path, region=(clip.x(), clip.y(), clip.width(), clip.height())
    )
    return (full_path, clip_path)


def take_screenshot_clip_only(folder: str, clip: skia.Rect):
    path = get_path(folder, "screenshot", "png", title="clip", dated=False, timed=False)
    pyautogui.screenshot(path, region=(clip.x(), clip.y(), clip.width(), clip.height()))
    return path


def locate_on_screen(path):
    """Wrapper around pyautogui.locateOnscreen. returns (left, top, width, height) or None"""
    try:
        return pyautogui.locateOnScreen(path, confidence=0.9, grayscale=True)
    except pyautogui.ImageNotFoundException:
        return None


def locate(path, path2):
    """Wrapper around pyautogui.locate. returns (left, top, width, height) or None"""
    try:
        return pyautogui.locate(path, path2, confidence=0.9, grayscale=True)
    except pyautogui.ImageNotFoundException:
        return None


def screen_changed(folder, paths, regions):
    for i, path in enumerate(paths):
        path2 = get_path(folder, "screenshot", "png", title=f"watch_{i}_test")
        pyautogui.screenshot(path2, region=regions[i])
        if not locate(path, path2):
            return True
    return False
