from typing import Dict, Optional

from .frame import Frame, TextFrame

FRIENDLY_NAMES = {
    "TIT2": "title",
    "TPE1": "artist",
    "TRCK": "track",
    "TALB": "album",
    "TPOS": "disc",
    "TCON": "genre",
    "TDAT": "date",
    "TYER": "year",
    "TOWN": "owner",
    "TPE2": "album_artist",
    "TSRC": "isrc",
    "TPUB": "publisher",
    "APIC": "picture",
}


class Tag:
    def __init__(self, frames: Optional[Dict[str, Frame]] = None):
        self.frames: Dict[str, Frame] = frames or {}

    def get(self, key):
        return self.frames.get(key)

    def set(self, key, value):
        self.frames[key] = value


def _make_property(frame_id):
    def getter(self):
        frame = self.frames.get(frame_id)
        if isinstance(frame, TextFrame):
            return frame.text
        return frame

    def setter(self, value):
        if isinstance(value, str):
            self.frames[frame_id] = TextFrame(frame_id=frame_id, text=value)
        else:
            self.frames[frame_id] = value

    return property(getter, setter)


def _install_accessors() -> None:
    for frame_id, friendly in FRIENDLY_NAMES.items():
        prop = _make_property(frame_id)
        setattr(Tag, frame_id, prop)
        setattr(Tag, friendly, prop)


_install_accessors()
