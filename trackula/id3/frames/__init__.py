from typing import Callable, Dict, Iterable

from ...frame import (
    CommentFrame,
    Frame,
    FrameCollection,
    GeneralObjectFrame,
    LyricsFrame,
    PictureFrame,
    PlayCountFrame,
    PopularimeterFrame,
    SyncedLyricsFrame,
    TextFrame,
    UniqueFileIdentifierFrame,
    UnknownFrame,
    UrlFrame,
    UserTextFrame,
    UserUrlFrame,
)
from ..synchsafe import decode_int, encode_int
from .comment import build_comment, parse_comment
from .geob import build_general_object, parse_general_object
from .lyrics import (
    build_lyrics,
    build_synced_lyrics,
    parse_lyrics,
    parse_synced_lyrics,
)
from .pcnt import build_play_count, parse_play_count
from .picture import build_picture, parse_picture
from .popm import build_popularimeter, parse_popularimeter
from .text import build_text, parse_text
from .ufid import build_ufid, parse_ufid
from .unknown import build_unknown, parse_unknown
from .url import build_url, build_user_url, parse_url, parse_user_url
from .user_text import build_user_text, parse_user_text

FRAME_HEADER_SIZE = 10

ParseFn = Callable[[str, bytes], Frame]

# Explicit per-frame-id parser mappings (takes precedence over prefix rules).
_EXACT_PARSERS: Dict[str, ParseFn] = {
    "APIC": parse_picture,
    "COMM": parse_comment,
    "GEOB": parse_general_object,
    "PCNT": parse_play_count,
    "POPM": parse_popularimeter,
    "SYLT": parse_synced_lyrics,
    "TXXX": parse_user_text,
    "UFID": parse_ufid,
    "USLT": parse_lyrics,
    "WXXX": parse_user_url,
}


def _lookup_parser(frame_id: str) -> ParseFn:
    if frame_id in _EXACT_PARSERS:
        return _EXACT_PARSERS[frame_id]
    # Text frames: T??? except TXXX (handled in the exact registry above).
    if frame_id.startswith("T") and frame_id != "TXXX":
        return parse_text
    # URL frames: W??? except WXXX (handled in the exact registry above).
    if frame_id.startswith("W"):
        return parse_url
    return parse_unknown


def parse_frames(data: bytes, version: int) -> FrameCollection:
    # each frame consists of a frame header followed by the actual frame data
    # frame header (10 bytes in v2.3 and v2.4)
    # frame id: 4 bytes - unique identifier eg. TIT2 (Title), TPE1 (Artist)
    # size:     4 bytes - size of the data part of the frame, excluding header
    # flags:    2 bytes - compression, encryption, or read-only status
    frames = FrameCollection()
    offset = 0
    length = len(data)

    while offset + FRAME_HEADER_SIZE <= length:
        header = data[offset:offset + FRAME_HEADER_SIZE]

        if header.strip(b"\x00") == b"":
            break

        frame_id = header[:4].decode("latin1")
        size_bytes = header[4:8]
        size = decode_int(size_bytes, synchsafe=(version == 4))

        frame_data = data[
            offset + FRAME_HEADER_SIZE : offset + FRAME_HEADER_SIZE + size
        ]

        parser = _lookup_parser(frame_id)
        frames.add(parser(frame_id, frame_data))

        offset += FRAME_HEADER_SIZE + size

    return frames


def build_frames(frames, version: int = 4) -> bytes:
    """Build a sequence of frames from any iterable of Frame instances.

    Accepts FrameCollection, list[Frame], or {id: Frame} dicts (for backward
    compatibility with callers that still pass dicts).
    """
    if isinstance(frames, dict):
        frame_iter: Iterable[Frame] = frames.values()
    else:
        frame_iter = frames

    out = b""
    for frame in frame_iter:
        out += build_frame(frame, version=version)
    return out


# Type-to-builder lookup. Used by build_frame so that adding a new frame type
# is one entry here plus the parser registration above, rather than growing an
# isinstance chain.
_BUILDERS = {
    TextFrame: build_text,
    UserTextFrame: build_user_text,
    PictureFrame: build_picture,
    CommentFrame: build_comment,
    LyricsFrame: build_lyrics,
    SyncedLyricsFrame: build_synced_lyrics,
    PopularimeterFrame: build_popularimeter,
    UniqueFileIdentifierFrame: build_ufid,
    PlayCountFrame: build_play_count,
    GeneralObjectFrame: build_general_object,
    UserUrlFrame: build_user_url,
    UrlFrame: build_url,
    UnknownFrame: build_unknown,
}


def build_frame(frame: Frame, version: int = 4) -> bytes:
    builder = _BUILDERS.get(type(frame))
    if builder is None:
        raise ValueError(f"Unsupported frame type: {type(frame).__name__}")
    encoded = builder(frame)

    size = encode_int(len(encoded), synchsafe=(version == 4))
    flags = b"\x00\x00"

    return frame.frame_id.encode() + size + flags + encoded
