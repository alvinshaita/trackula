from ..errors import InvalidHeaderError
from .frames import parse_frames
from .header import HEADER_SIZE, parse_header
from .synchsafe import decode_synchsafe

# bit 6 of the main header flags byte indicates presence of an extended header
EXTENDED_HEADER_FLAG = 0x40


def parse_id3(data: bytes) -> dict:
    header = parse_header(data[:HEADER_SIZE])

    content = data[HEADER_SIZE : HEADER_SIZE + header["size"]]

    ext_len = _extended_header_length(
        content, header["version"], header["flags"]
    )

    frames_body = content[ext_len:]
    frames = parse_frames(frames_body, header["version"])

    return {
        "header": header,
        "frames": frames,
    }


def _extended_header_length(content: bytes, version: int, flags: int) -> int:
    """Return the byte length of the extended header at the start of `content`.

    `content` is the tag body immediately after the 10-byte main header, i.e.
    what the main header's size field describes. Returns 0 if the extended
    header flag is not set.

    The two spec versions differ:

    - v2.4: the first 4 bytes hold a synchsafe integer whose value is the
      total extended header size INCLUDING those 4 size bytes.
    - v2.3: the first 4 bytes hold a plain big-endian integer whose value
      is the size EXCLUDING those 4 bytes, so the true byte length is
      4 + <value>.

    Raises InvalidHeaderError if the extended header is truncated or claims
    a length larger than the tag body.
    """
    if not flags & EXTENDED_HEADER_FLAG:
        return 0

    if len(content) < 4:
        raise InvalidHeaderError(
            "Extended header truncated — fewer than 4 size bytes"
        )

    if version >= 4:
        length = decode_synchsafe(content[:4])
    else:
        length = 4 + int.from_bytes(content[:4], "big")

    if length > len(content):
        raise InvalidHeaderError(
            f"Extended header length {length} exceeds tag content size "
            f"{len(content)}"
        )

    return length
