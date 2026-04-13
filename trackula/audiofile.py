from typing import Optional

from .containers.mp3 import split_mp3, write_mp3
from .id3.builder import build_id3
from .id3.parser import parse_id3
from .tag import Tag


class AudioFile:
    def __init__(self, path: str):
        self.path = path
        tag_bytes, self._audio_bytes = split_mp3(path)
        frames = parse_id3(tag_bytes)["frames"] if tag_bytes else {}
        self.tag = Tag(frames)

    def save(self, output: Optional[str] = None) -> None:
        target = output or self.path
        tag_bytes = build_id3(self.tag.frames)
        write_mp3(target, tag_bytes, self._audio_bytes)

    def __repr__(self) -> str:
        return f"AudioFile({self.path!r})"
