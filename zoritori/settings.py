from pathlib import Path

from zoritori.types import Root, Box
from zoritori.files import load_json, save_json


def get_settings_path():
    dot_zoritori = Path.home() / ".zoritori"
    Path(dot_zoritori).mkdir(parents=True, exist_ok=True)
    return dot_zoritori / "settings.json"


def load_clips(path):
    settings = load_json(path)
    if settings and "clips" in settings:
        clips = settings["clips"]
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
    settings = load_json(path)
    if not settings:
        settings = {}
    settings["clips"] = clips
    save_json(path, settings)
