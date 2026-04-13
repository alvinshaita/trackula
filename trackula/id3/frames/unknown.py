from ...frame import UnknownFrame


def parse_unknown(frame_id: str, data: bytes) -> UnknownFrame:
    return UnknownFrame(frame_id=frame_id, raw=data)


def build_unknown(frame: UnknownFrame) -> bytes:
    return frame.raw
