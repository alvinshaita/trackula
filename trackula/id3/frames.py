from .encoding import decode_text, encode_text
from .synchsafe import decode_int, encode_int

FRAME_HEADER_SIZE = 10


def parse_frames(data: bytes, version: int) -> dict:
    # each frame consists of a frame header followed by the actual frame data
    # frame header (10 bytes in v2.3 and v2.4)
    # frame id: 4 bytes - unique identifier eg. TIT2 (Title), TPE1 (Artist)
    # size:     4 bytes - size of the data part of the frame, excluding header
    # flags:    2 bytes - compression, encryption, or read-only status

    frames = {}
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
            frames[frame_id] = decode_text(frame_data)
        else:
            frames[frame_id] = frame_data

        offset += FRAME_HEADER_SIZE + size

    return frames


def build_frames(frames: dict, version: int = 4) -> bytes:
    out = b""
    for frame_id, frame_data in frames.items():
        out += build_frame(frame_id, frame_data, version=version)
    return out


def build_frame(frame_id: str, frame_data, version: int = 4) -> bytes:
    if frame_id.startswith("T"):
        encoded = encode_text(frame_data, 1)
    else:
        encoded = frame_data

    size = encode_int(len(encoded), synchsafe=(version == 4))
    flags = b"\x00\x00"

    return frame_id.encode() + size + flags + encoded
