from typing import Dict

from ..frame import Frame, TextFrame, UnknownFrame
from .encoding import decode_text, encode_text
from .synchsafe import decode_int, encode_int

FRAME_HEADER_SIZE = 10


def parse_frames(data: bytes, version: int) -> Dict[str, Frame]:
    # each frame consists of a frame header followed by the actual frame data
    # frame header (10 bytes in v2.3 and v2.4)
    # frame id: 4 bytes - unique identifier eg. TIT2 (Title), TPE1 (Artist)
    # size:     4 bytes - size of the data part of the frame, excluding header
    # flags:    2 bytes - compression, encryption, or read-only status

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
        if frame_id.startswith("T"):
            frames[frame_id] = TextFrame(
                frame_id=frame_id,
                text=decode_text(frame_data),
            )
        else:
            frames[frame_id] = UnknownFrame(frame_id=frame_id, raw=frame_data)

        offset += FRAME_HEADER_SIZE + size

    return frames


def build_frames(frames: Dict[str, Frame], version: int = 4) -> bytes:
    out = b""
    for frame in frames.values():
        out += build_frame(frame, version=version)
    return out


def build_frame(frame: Frame, version: int = 4) -> bytes:
    if isinstance(frame, TextFrame):
        encoded = encode_text(frame.text, 1)
    elif isinstance(frame, UnknownFrame):
        encoded = frame.raw
    else:
        raise ValueError(f"Unsupported frame type: {type(frame).__name__}")

    size = encode_int(len(encoded), synchsafe=(version == 4))
    flags = b"\x00\x00"

    return frame.frame_id.encode() + size + flags + encoded
