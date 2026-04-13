from .frames import build_frames
from .header import build_header


def build_id3(frames: dict, version: int = 4) -> bytes:
    frame_bytes = build_frames(frames, version=version)
    return build_header(len(frame_bytes), version=version) + frame_bytes
