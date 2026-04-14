from ...frame import UserTextFrame
from ..encoding import (
    decode_by_encoding,
    encode_by_encoding,
    find_terminator,
    terminator_length,
)


def parse_user_text(frame_id: str, data: bytes) -> UserTextFrame:
    # TXXX structure:
    #   encoding     1 byte
    #   description  text in `encoding`, null-terminated
    #   text (value) text in `encoding`, rest of frame
    encoding = data[0]

    desc_start = 1
    desc_end = find_terminator(data, desc_start, encoding)
    description = decode_by_encoding(data[desc_start:desc_end], encoding)

    text_start = desc_end + terminator_length(encoding)
    text = decode_by_encoding(data[text_start:], encoding)

    return UserTextFrame(
        frame_id=frame_id,
        description=description,
        text=text,
    )


def build_user_text(frame: UserTextFrame) -> bytes:
    # Use encoding 3 (UTF-8).
    return (
        b"\x03"
        + encode_by_encoding(frame.description, 3)
        + b"\x00"
        + encode_by_encoding(frame.text, 3)
    )
