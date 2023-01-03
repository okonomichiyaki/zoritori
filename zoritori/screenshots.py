import logging
import pyautogui
from pathlib import Path

from zoritori.files import get_path
from zoritori.types import CharacterData, Box


_logger = logging.getLogger("zoritori")


def take_watch_screenshot(folder, regions):
    watch_paths = []
    for i, region in enumerate(regions):
        watch_path = get_path(folder, "screenshot", "png", title=f"watch_{i}_base")
        Path(watch_path).unlink(missing_ok=True)
        pyautogui.screenshot(watch_path, region=region)
        watch_paths.append(watch_path)
    return watch_paths


def take_screenshots(folder: str, clip: Box):
    full_path = get_path(
        folder, "screenshot", "png", title="xxxxx", dated=True, timed=True
    )
    pyautogui.screenshot(full_path)
    clip_path = get_path(folder, "screenshot", "png", title="text")
    pyautogui.screenshot(
        clip_path, region=(clip.screenx, clip.screeny, clip.width, clip.height)
    )
    return (full_path, clip_path)


def take_fullscreen_screenshot(folder: str):
    full_path = get_path(
        folder, "screenshot", "png", title="xxxxx", dated=True, timed=True
    )
    pyautogui.screenshot(full_path)
    return full_path


def take_screenshot_clip_only(folder: str, clip: Box):
    path = get_path(folder, "screenshot", "png", title="clip", dated=False, timed=False)
    pyautogui.screenshot(
        path, region=(clip.screenx, clip.screeny, clip.width, clip.height)
    )
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
        Path(path2).unlink(missing_ok=True)
        pyautogui.screenshot(path2, region=regions[i])
        if not locate(path, path2):
            return True
    return False
