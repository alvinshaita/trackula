import pytest

from trackula.frame import TextFrame
from trackula.id3.frames import build_frame
from trackula.id3.parser import parse_id3
from trackula.id3.synchsafe import encode_synchsafe

EXT_HEADER_FLAG = b"\x40"
NO_FLAGS = b"\x00"


def _wrap_tag(version: int, flags_byte: bytes, content: bytes) -> bytes:
    """Assemble an ID3 tag from a pre-built content body.

    We synthesize the main header here rather than going through build_id3
    because build_id3 never emits the extended-header flag, so these tests
    need direct byte control.
    """
    header = (
        b"ID3"
        + bytes([version, 0])
        + flags_byte
        + encode_synchsafe(len(content))
    )
    return header + content


def _v24_ext_header_empty() -> bytes:
    # v2.4 minimum extended header = 6 bytes total:
    #   4 bytes synchsafe size (value = 6, including these 4 bytes)
    #   1 byte  number-of-flag-bytes (always 1)
    #   1 byte  extended flags
    return encode_synchsafe(6) + b"\x01" + b"\x00"


def _v23_ext_header_empty() -> bytes:
    # v2.3 minimum extended header = 10 bytes total:
    #   4 bytes big-endian size (value = 6, EXCLUDING these 4 size bytes)
    #   2 bytes extended flags (no CRC)
    #   4 bytes padding size
    return (6).to_bytes(4, "big") + b"\x00\x00" + (0).to_bytes(4, "big")


def _v23_ext_header_with_crc() -> bytes:
    # v2.3 extended header with CRC = 14 bytes total:
    #   4 bytes big-endian size (value = 10)
    #   2 bytes ext flags (CRC bit set — MSB of first flag byte)
    #   4 bytes padding size
    #   4 bytes CRC-32 of the frame data
    return (
        (10).to_bytes(4, "big")
        + b"\x80\x00"
        + (0).to_bytes(4, "big")
        + (0xDEADBEEF).to_bytes(4, "big")
    )


class TestV24ExtendedHeader:
    def test_tag_with_empty_ext_header_parses(self):
        frame_bytes = build_frame(TextFrame("TIT2", "Hello"), version=4)
        content = _v24_ext_header_empty() + frame_bytes
        tag = _wrap_tag(4, EXT_HEADER_FLAG, content)

        parsed = parse_id3(tag)
        assert parsed["frames"]["TIT2"].text == "Hello"

    def test_tag_with_larger_ext_header(self):
        # Oversized but valid: the size field says 12 bytes and we pad the
        # extra 6 bytes with zeros. Spec allows extended headers to contain
        # unrecognized trailing data.
        ext = encode_synchsafe(12) + b"\x01" + b"\x00" + b"\x00" * 6
        frame_bytes = build_frame(TextFrame("TIT2", "Hello"), version=4)
        content = ext + frame_bytes
        tag = _wrap_tag(4, EXT_HEADER_FLAG, content)

        parsed = parse_id3(tag)
        assert parsed["frames"]["TIT2"].text == "Hello"

    def test_multiple_frames_after_ext_header(self):
        frames = (
            build_frame(TextFrame("TIT2", "Title"), version=4)
            + build_frame(TextFrame("TPE1", "Artist"), version=4)
            + build_frame(TextFrame("TALB", "Album"), version=4)
        )
        content = _v24_ext_header_empty() + frames
        tag = _wrap_tag(4, EXT_HEADER_FLAG, content)

        parsed = parse_id3(tag)
        assert parsed["frames"]["TIT2"].text == "Title"
        assert parsed["frames"]["TPE1"].text == "Artist"
        assert parsed["frames"]["TALB"].text == "Album"


class TestV23ExtendedHeader:
    def test_tag_with_empty_ext_header_parses(self):
        frame_bytes = build_frame(TextFrame("TIT2", "Hello"), version=3)
        content = _v23_ext_header_empty() + frame_bytes
        tag = _wrap_tag(3, EXT_HEADER_FLAG, content)

        parsed = parse_id3(tag)
        assert parsed["frames"]["TIT2"].text == "Hello"

    def test_tag_with_crc_ext_header_parses(self):
        # The 4-byte CRC value is NOT validated — we just skip past it.
        frame_bytes = build_frame(TextFrame("TIT2", "Hello"), version=3)
        content = _v23_ext_header_with_crc() + frame_bytes
        tag = _wrap_tag(3, EXT_HEADER_FLAG, content)

        parsed = parse_id3(tag)
        assert parsed["frames"]["TIT2"].text == "Hello"

    def test_multiple_frames_after_crc_ext_header(self):
        frames = (
            build_frame(TextFrame("TIT2", "Title"), version=3)
            + build_frame(TextFrame("TPE1", "Artist"), version=3)
        )
        content = _v23_ext_header_with_crc() + frames
        tag = _wrap_tag(3, EXT_HEADER_FLAG, content)

        parsed = parse_id3(tag)
        assert parsed["frames"]["TIT2"].text == "Title"
        assert parsed["frames"]["TPE1"].text == "Artist"


class TestNoExtendedHeader:
    def test_flag_unset_is_regression_guard(self):
        # The common case: main-header flag byte is 0x00, no ext header,
        # the first 10 bytes of content are the first frame's header.
        frame_bytes = build_frame(TextFrame("TIT2", "Hello"), version=4)
        tag = _wrap_tag(4, NO_FLAGS, frame_bytes)

        parsed = parse_id3(tag)
        assert parsed["frames"]["TIT2"].text == "Hello"

    def test_unrelated_flag_bits_are_tolerated(self):
        # Set the experimental indicator (bit 5) but NOT the extended header
        # flag. We should still skip extended header parsing.
        frame_bytes = build_frame(TextFrame("TIT2", "Hello"), version=4)
        tag = _wrap_tag(4, b"\x20", frame_bytes)

        parsed = parse_id3(tag)
        assert parsed["frames"]["TIT2"].text == "Hello"


class TestStaleExtendedHeaderFlag:
    """Scenarios where the flag is set but the bytes don't actually form an
    extended header. trackula recovers by treating the flag as stale and
    parsing content from offset 0 rather than raising."""

    def test_frames_begin_immediately_after_stale_flag_v24(self):
        # A buggy tagger set the flag but didn't write the extended header.
        # content[:4] is really the frame id of the first frame.
        frame_bytes = build_frame(TextFrame("TIT2", "Hello"), version=4)
        tag = _wrap_tag(4, EXT_HEADER_FLAG, frame_bytes)

        parsed = parse_id3(tag)
        assert parsed["frames"]["TIT2"].text == "Hello"

    def test_frames_begin_immediately_after_stale_flag_v23(self):
        frame_bytes = build_frame(TextFrame("TPE1", "Artist"), version=3)
        tag = _wrap_tag(3, EXT_HEADER_FLAG, frame_bytes)

        parsed = parse_id3(tag)
        assert parsed["frames"]["TPE1"].text == "Artist"

    def test_multi_frame_recovery_when_flag_is_stale(self):
        frame_bytes = (
            build_frame(TextFrame("TIT2", "Title"), version=4)
            + build_frame(TextFrame("TPE1", "Artist"), version=4)
            + build_frame(TextFrame("TALB", "Album"), version=4)
        )
        tag = _wrap_tag(4, EXT_HEADER_FLAG, frame_bytes)

        parsed = parse_id3(tag)
        assert parsed["frames"]["TIT2"].text == "Title"
        assert parsed["frames"]["TPE1"].text == "Artist"
        assert parsed["frames"]["TALB"].text == "Album"

    def test_truncated_content_falls_back_gracefully(self):
        # Flag set but content too short for the 4-byte size field.
        # Should not crash — treat the flag as stale, parse empty content.
        tag = _wrap_tag(4, EXT_HEADER_FLAG, b"\x00\x00")
        parsed = parse_id3(tag)
        assert len(parsed["frames"]) == 0

    def test_size_below_minimum_falls_back(self):
        # v2.4 ext header minimum is 6 bytes. Claim 2.
        content = encode_synchsafe(2) + b"\x00\x00\x00\x00"
        tag = _wrap_tag(4, EXT_HEADER_FLAG, content)
        parsed = parse_id3(tag)
        # Falls back to parsing content as frames. The bytes don't form
        # a valid frame, so we get an empty result — but no crash.
        assert len(parsed["frames"]) == 0

    def test_size_exceeds_content_falls_back_v24(self):
        # Claim 100-byte ext header in a short content body. 4 bytes is
        # below the frame header size, so parse_frames finds nothing.
        bogus = encode_synchsafe(100)
        tag = _wrap_tag(4, EXT_HEADER_FLAG, bogus)
        parsed = parse_id3(tag)
        assert len(parsed["frames"]) == 0

    def test_size_exceeds_content_falls_back_v23(self):
        bogus = (100).to_bytes(4, "big") + b"\x00\x00"
        tag = _wrap_tag(3, EXT_HEADER_FLAG, bogus)
        parsed = parse_id3(tag)
        assert len(parsed["frames"]) == 0
