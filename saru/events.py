class Event:
    def get_key(self):
        return None

    def get_clip(self):
        return None


class KeyEvent(Event):
    def __init__(self, key):
        self._key = key

    def get_key(self):
        return self._key


class ClipEvent(Event):
    def __init__(self, clip):
        self._clip = clip

    def get_clip(self):
        return self._clip
