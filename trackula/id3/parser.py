from .frames import parse_frames
from .header import HEADER_SIZE, parse_header
from .synchsafe import decode_synchsafe

# bit 6 of the main header flags byte indicates presence of an extended header
EXTENDED_HEADER_FLAG = 0x40

# Minimum valid total length of an extended header, by spec version. If the
# claimed length is below this the flag is almost certainly stale.
_V24_MIN_EXT_HEADER = 6   # 4 size bytes + 1 numflags + 1 flags
_V23_MIN_EXT_HEADER = 10  # 4 size bytes + 2 flags + 4 padding size


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

    `content` is the tag body immediately after the 10-byte main header.
    Returns 0 if the extended header flag is not set OR if the claimed
    extended header length looks implausible — trackula prefers leniency
    over strictness here because stale flags set by buggy taggers are
    more common in real-world files than actual extended headers we
    should strictly validate.

    Fall-through cases (all return 0 rather than raising):

    - flag bit is not set
    - content is too short to hold even the 4-byte size field
    - claimed length is below the minimum valid size for the version
    - claimed length is larger than the remaining tag body
    - the first 4 bytes of content look like a real frame id (A-Z, 0-9),
      which is a strong signal the flag is stale and frames begin
      immediately after the main header

    Otherwise returns the claimed length per spec:

    - v2.4: synchsafe integer in the first 4 bytes, INCLUDING those
      4 bytes in the total.
    - v2.3: plain big-endian integer in the first 4 bytes, EXCLUDING
      those 4 bytes, so the true length is 4 + value.
    """
    if not flags & EXTENDED_HEADER_FLAG:
        return 0

    if len(content) < 4:
        return 0

    if version >= 4:
        length = decode_synchsafe(content[:4])
        minimum = _V24_MIN_EXT_HEADER
    else:
        length = 4 + int.from_bytes(content[:4], "big")
        minimum = _V23_MIN_EXT_HEADER

    if length < minimum or length > len(content):
        return 0

    # Independent signal: the ext header "size" bytes happen to look exactly
    # like a valid frame id (4 bytes of ASCII uppercase or digit). The length
    # check above would catch this for normal-sized tags because "TIT2" as a
    # synchsafe integer is ~177 MB, far larger than any realistic content.
    # This belt-and-suspenders check handles the pathological case where the
    # tag body is large enough that the decoded value happens to fit.
    if _looks_like_frame_id(content[:4]):
        return 0

    return length


def _looks_like_frame_id(data: bytes) -> bool:
    """Return True if the 4 bytes look like a valid ID3v2 frame id.

    Frame ids are 4 bytes of ASCII uppercase letters (0x41-0x5A) and
    digits (0x30-0x39) per the ID3v2 spec.
    """
    if len(data) != 4:
        return False
    return all(
        (0x30 <= b <= 0x39) or (0x41 <= b <= 0x5A) for b in data
    )
