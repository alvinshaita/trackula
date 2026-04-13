from ...frame import PictureFrame
from ..encoding import (
    decode_by_encoding,
    encode_by_encoding,
    find_terminator,
    terminator_length,
)


def parse_picture(frame_id: str, data: bytes) -> PictureFrame:
    # Structure:
    #   encoding      1 byte
    #   mime type     latin-1, null-terminated
    #   picture type  1 byte (enum, 0x00..0x14)
    #   description   text in `encoding`, null-terminated
    #   picture data  binary, rest of frame
    encoding = data[0]

    mime_end = data.index(b"\x00", 1)
    mime = data[1:mime_end].decode("latin1")

    picture_type = data[mime_end + 1]

    desc_start = mime_end + 2
    desc_end = find_terminator(data, desc_start, encoding)
    description = decode_by_encoding(data[desc_start:desc_end], encoding)

    pic_start = desc_end + terminator_length(encoding)
    picture_data = data[pic_start:]

    return PictureFrame(
        frame_id=frame_id,
        mime=mime,
        picture_type=picture_type,
        description=description,
        data=picture_data,
    )


def build_picture(frame: PictureFrame) -> bytes:
    # We build with encoding 3 (UTF-8) for the description.
    # MIME type is always latin-1 by spec.
    return (
        b"\x03"
        + frame.mime.encode("latin1")
        + b"\x00"
        + bytes([frame.picture_type])
        + encode_by_encoding(frame.description, 3)
        + b"\x00"
        + frame.data
    )
