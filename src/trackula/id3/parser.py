from .frames import parse_frames
from .header import HEADER_SIZE, parse_header


def parse_id3(data: bytes) -> dict:
    header = parse_header(data[:HEADER_SIZE])

    # TODO: extended headers awareness
    frames_body = data[HEADER_SIZE : HEADER_SIZE + header["size"]]
    frames = parse_frames(frames_body, header["version"])

    return {
        "header": header,
        "frames": frames,
    }
