from dataclasses import fields
from typing import Iterable, List, Optional, Union

from .frame import Frame, FrameCollection, GeneralObjectFrame, PictureFrame, TextFrame

GEOB_DATA_PREVIEW_LIMIT = 50

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
    def __init__(
        self,
        frames: Optional[Union[FrameCollection, Iterable[Frame], dict]] = None,
    ):
        if frames is None:
            self.frames = FrameCollection()
        elif isinstance(frames, FrameCollection):
            self.frames = frames
        elif isinstance(frames, dict):
            # Backward compat for callers that pass {id: frame} dicts.
            self.frames = FrameCollection(frames.values())
        else:
            self.frames = FrameCollection(frames)

    def get(self, key):
        return self.frames.get(key)

    def set(self, key, value):
        self.frames[key] = value

    def summary(self) -> List[dict]:
        """Return one dict per frame describing every tag on the track.

        Each dict carries every dataclass field of the frame, in declaration
        order, so frames with the same id (multiple COMM, multiple APIC)
        still show up as distinct entries. Binary payloads that would spam
        the terminal are elided:

        - APIC: `data` is always replaced with `"..."`.
        - GEOB: `data` is replaced with `"..."` only when longer than
          GEOB_DATA_PREVIEW_LIMIT bytes; short payloads are shown as-is.
        """
        return [_frame_summary(frame) for frame in self.frames]


def _frame_summary(frame: Frame) -> dict:
    entry = {}
    for f in fields(frame):
        value = getattr(frame, f.name)
        if isinstance(frame, PictureFrame) and f.name == "data":
            entry[f.name] = "..."
        elif (
            isinstance(frame, GeneralObjectFrame)
            and f.name == "data"
            and len(value) > GEOB_DATA_PREVIEW_LIMIT
        ):
            entry[f.name] = "..."
        else:
            entry[f.name] = value
    return entry


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
