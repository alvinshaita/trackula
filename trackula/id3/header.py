from struct import unpack

from ..errors import InvalidHeaderError
from .synchsafe import decode_int, encode_int

HEADER_SIZE = 10


def parse_header(data: bytes) -> dict:
    # main header is always 10 bytes long
    # in ID3v2, header is located at the beginning of the file
    # identifier: 3 bytes - always "ID3"
    # version:    2 bytes - major version and revision eg. 03 00 for v2.3.0
    # flags:      1 byte  - bitwise indicator
    # size:       4 bytes - total size of the tag, excluding 10 byte header

    if len(data) < HEADER_SIZE:
        raise InvalidHeaderError("ID3 header data too short")

    identifier, version, revision, flags, size_bytes = unpack(">3sBBB4s", data)
    if identifier != b"ID3":
        raise InvalidHeaderError("Missing ID3 identifier")

    size = decode_int(size_bytes, synchsafe=True)

    return {
        "version": version,
        "revision": revision,
        "flags": flags,
        "size": size,
    }


def build_header(size: int, version: int = 4) -> bytes:
    # ID3 tag size is ALWAYS synchsafe (v2.3 + v2.4)
    return (
        b"ID3"
        + bytes([version, 0])
        + b"\x00"
        + encode_int(size, synchsafe=True)
    )
