from ...frame import TextFrame
from ..encoding import decode_text, encode_text


def parse_text(frame_id: str, data: bytes) -> TextFrame:
    return TextFrame(frame_id=frame_id, text=decode_text(data))


def build_text(frame: TextFrame) -> bytes:
    # encoding 1 = UTF-16 with BOM — valid in both v2.3 and v2.4
    return encode_text(frame.text, encoding=1)
