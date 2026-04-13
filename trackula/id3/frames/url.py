from ...frame import UrlFrame, UserUrlFrame
from ..encoding import (
    decode_by_encoding,
    encode_by_encoding,
    find_terminator,
    terminator_length,
)


def parse_url(frame_id: str, data: bytes) -> UrlFrame:
    # W??? frames (except WXXX) are always latin-1 URLs with no encoding byte.
    return UrlFrame(frame_id=frame_id, url=data.decode("latin1"))


def build_url(frame: UrlFrame) -> bytes:
    return frame.url.encode("latin1")


def parse_user_url(frame_id: str, data: bytes) -> UserUrlFrame:
    # WXXX structure:
    #   encoding     1 byte
    #   description  text in `encoding`, null-terminated
    #   url          latin-1 text, rest of frame
    encoding = data[0]

    desc_start = 1
    desc_end = find_terminator(data, desc_start, encoding)
    description = decode_by_encoding(data[desc_start:desc_end], encoding)

    url_start = desc_end + terminator_length(encoding)
    url = data[url_start:].decode("latin1")

    return UserUrlFrame(
        frame_id=frame_id,
        description=description,
        url=url,
    )


def build_user_url(frame: UserUrlFrame) -> bytes:
    return (
        b"\x03"
        + encode_by_encoding(frame.description, 3)
        + b"\x00"
        + frame.url.encode("latin1")
    )
