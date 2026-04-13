from ...frame import CommentFrame
from ..encoding import (
    decode_by_encoding,
    encode_by_encoding,
    find_terminator,
    terminator_length,
)


def parse_comment(frame_id: str, data: bytes) -> CommentFrame:
    # Structure:
    #   encoding     1 byte
    #   language     3 bytes (ISO-639-2, latin-1)
    #   description  text in `encoding`, null-terminated
    #   text         text in `encoding`, rest of frame
    encoding = data[0]
    language = data[1:4].decode("latin1")

    desc_start = 4
    desc_end = find_terminator(data, desc_start, encoding)
    description = decode_by_encoding(data[desc_start:desc_end], encoding)

    text_start = desc_end + terminator_length(encoding)
    text = decode_by_encoding(data[text_start:], encoding)

    return CommentFrame(
        frame_id=frame_id,
        language=language,
        description=description,
        text=text,
    )


def build_comment(frame: CommentFrame) -> bytes:
    # Use encoding 3 (UTF-8) for description + text.
    language = (frame.language[:3] + "\x00\x00\x00")[:3].encode("latin1")
    return (
        b"\x03"
        + language
        + encode_by_encoding(frame.description, 3)
        + b"\x00"
        + encode_by_encoding(frame.text, 3)
    )
