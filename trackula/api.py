from .containers.mp3 import parse_v1_tag, split_mp3, write_mp3
from .id3.builder import build_id3
from .id3.parser import parse_id3
from .tag import Tag


def read(path: str) -> Tag:
    split = split_mp3(path)
    if split.v2_tag:
        parsed = parse_id3(split.v2_tag)
        return Tag(parsed["frames"])
    if split.v1_tag:
        return Tag(parse_v1_tag(split.v1_tag))
    return Tag()


def write(path: str, tag: Tag) -> None:
    """Update the ID3 tag of an existing MP3 in place. `path` must exist.

    Writes a fresh ID3v2 tag followed by the pure audio body. Any ID3v1
    footer the source file carried is dropped — the v2 tag supersedes it.
    """
    split = split_mp3(path)
    tag_bytes = build_id3(tag.frames)
    write_mp3(path, tag_bytes, split.audio)
