from .containers.mp3 import split_mp3, write_mp3
from .id3.builder import build_id3
from .id3.parser import parse_id3
from .tag import Tag


def read(path: str) -> Tag:
    tag_bytes, _ = split_mp3(path)
    if not tag_bytes:
        return Tag()
    parsed = parse_id3(tag_bytes)
    return Tag(parsed["frames"])


def write(path: str, tag: Tag) -> None:
    _, audio_bytes = split_mp3(path)
    tag_bytes = build_id3(tag.frames)
    write_mp3(path, tag_bytes, audio_bytes)
