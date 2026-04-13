from typing import Callable, Dict, Tuple

from ...frame import (
    CommentFrame,
    Frame,
    PictureFrame,
    TextFrame,
    UnknownFrame,
    UrlFrame,
    UserUrlFrame,
)
from ..synchsafe import decode_int, encode_int
from .comment import build_comment, parse_comment
from .picture import build_picture, parse_picture
from .text import build_text, parse_text
from .unknown import build_unknown, parse_unknown
from .url import build_url, build_user_url, parse_url, parse_user_url

FRAME_HEADER_SIZE = 10

ParseFn = Callable[[str, bytes], Frame]

# Explicit per-frame-id parser mappings (takes precedence over prefix rules).
_EXACT_PARSERS: Dict[str, ParseFn] = {
    "APIC": parse_picture,
    "COMM": parse_comment,
    "WXXX": parse_user_url,
}


def _lookup_parser(frame_id: str) -> ParseFn:
    if frame_id in _EXACT_PARSERS:
        return _EXACT_PARSERS[frame_id]
    # Text frames: T??? except TXXX (user-defined, treated as unknown for now)
    if frame_id.startswith("T") and frame_id != "TXXX":
        return parse_text
    # URL frames: W??? except WXXX (handled above)
    if frame_id.startswith("W"):
        return parse_url
    return parse_unknown


def parse_frames(data: bytes, version: int) -> Dict[str, Frame]:
    # each frame consists of a frame header followed by the actual frame data
    # frame header (10 bytes in v2.3 and v2.4)
    # frame id: 4 bytes - unique identifier eg. TIT2 (Title), TPE1 (Artist)
    # size:     4 bytes - size of the data part of the frame, excluding header
    # flags:    2 bytes - compression, encryption, or read-only status
    #
    # NOTE: multiple frames with the same id (COMM, WXXX, APIC with different
    # descriptors) can legally coexist in a tag. For now we store one per id
    # and last-one-wins; multi-frame support is a future refactor.
    frames: Dict[str, Frame] = {}
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
        frames[frame_id] = parser(frame_id, frame_data)

        offset += FRAME_HEADER_SIZE + size

    return frames


def build_frames(frames: Dict[str, Frame], version: int = 4) -> bytes:
    out = b""
    for frame in frames.values():
        out += build_frame(frame, version=version)
    return out


def build_frame(frame: Frame, version: int = 4) -> bytes:
    # Dispatch on the concrete Frame type — the dataclass carries its own
    # identity, which is more robust than dispatching on frame_id.
    if isinstance(frame, TextFrame):
        encoded = build_text(frame)
    elif isinstance(frame, PictureFrame):
        encoded = build_picture(frame)
    elif isinstance(frame, CommentFrame):
        encoded = build_comment(frame)
    elif isinstance(frame, UserUrlFrame):
        encoded = build_user_url(frame)
    elif isinstance(frame, UrlFrame):
        encoded = build_url(frame)
    elif isinstance(frame, UnknownFrame):
        encoded = build_unknown(frame)
    else:
        raise ValueError(f"Unsupported frame type: {type(frame).__name__}")

    size = encode_int(len(encoded), synchsafe=(version == 4))
    flags = b"\x00\x00"

    return frame.frame_id.encode() + size + flags + encoded
