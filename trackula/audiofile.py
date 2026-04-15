from typing import Optional

from .containers.mp3 import parse_v1_tag, split_mp3, write_mp3
from .id3.builder import build_id3
from .id3.parser import parse_id3
from .tag import Tag


class AudioFile:
    def __init__(self, path: str):
        self.path = path
        split = split_mp3(path)
        self._audio_bytes = split.audio

        if split.v2_tag:
            frames = parse_id3(split.v2_tag)["frames"]
        elif split.v1_tag:
            frames = parse_v1_tag(split.v1_tag)
        else:
            frames = None

        self.tag = Tag(frames)

    def save(self, output: Optional[str] = None) -> None:
        target = output or self.path
        tag_bytes = build_id3(self.tag.frames)
        write_mp3(target, tag_bytes, self._audio_bytes)

    def __repr__(self) -> str:
        return f"AudioFile({self.path!r})"
