from ...frame import GeneralObjectFrame
from ..encoding import (
    decode_by_encoding,
    encode_by_encoding,
    find_terminator,
    terminator_length,
)


def parse_general_object(frame_id: str, data: bytes) -> GeneralObjectFrame:
    # GEOB structure:
    #   encoding         1 byte
    #   MIME type        latin-1, null-terminated
    #   Filename         text in `encoding`, null-terminated
    #   Description      text in `encoding`, null-terminated
    #   Object           binary, rest of frame
    encoding = data[0]

    mime_end = data.index(b"\x00", 1)
    mime = data[1:mime_end].decode("latin1")

    filename_start = mime_end + 1
    filename_end = find_terminator(data, filename_start, encoding)
    filename = decode_by_encoding(data[filename_start:filename_end], encoding)

    desc_start = filename_end + terminator_length(encoding)
    desc_end = find_terminator(data, desc_start, encoding)
    description = decode_by_encoding(data[desc_start:desc_end], encoding)

    obj_start = desc_end + terminator_length(encoding)
    object_data = data[obj_start:]

    return GeneralObjectFrame(
        frame_id=frame_id,
        mime=mime,
        filename=filename,
        description=description,
        data=object_data,
    )


def build_general_object(frame: GeneralObjectFrame) -> bytes:
    return (
        b"\x03"  # UTF-8 encoding
        + frame.mime.encode("latin1")
        + b"\x00"
        + encode_by_encoding(frame.filename, 3)
        + b"\x00"
        + encode_by_encoding(frame.description, 3)
        + b"\x00"
        + frame.data
    )
