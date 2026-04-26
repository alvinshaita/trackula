import pytest

from trackula.frame import (
    FIELD_REPR_LIMIT,
    GeneralObjectFrame,
    PictureFrame,
    TextFrame,
    UnknownFrame,
)
from trackula.id3.frames import build_frame, build_frames, parse_frames


class TestBuildFrame:
    def test_text_frame_header(self):
        frame = TextFrame(frame_id="TIT2", text="Hello")
        result = build_frame(frame, version=4)
        assert result[:4] == b"TIT2"

    def test_unknown_frame_preserves_raw(self):
        frame = UnknownFrame(frame_id="PRIV", raw=b"\xff\xd8\xff\xe0")
        result = build_frame(frame, version=4)
        assert result[:4] == b"PRIV"
        assert result[-4:] == b"\xff\xd8\xff\xe0"

    def test_rejects_unsupported_type(self):
        with pytest.raises(ValueError, match="Unsupported frame type"):
            build_frame("not a frame")

    def test_rejects_raw_dict(self):
        # guards against the old dict-based contract regressing
        with pytest.raises(ValueError):
            build_frame({"frame_id": "TIT2", "text": "X"})


class TestParseFrames:
    def test_parse_empty(self):
        assert len(parse_frames(b"", version=4)) == 0

    def test_parse_text_frame(self):
        built = build_frames({"TIT2": TextFrame("TIT2", "Hello")}, version=4)
        parsed = parse_frames(built, version=4)
        assert "TIT2" in parsed
        assert isinstance(parsed["TIT2"], TextFrame)
        assert parsed["TIT2"].text == "Hello"
        assert parsed["TIT2"].frame_id == "TIT2"

    def test_parse_unknown_frame(self):
        built = build_frames(
            {"PRIV": UnknownFrame("PRIV", b"\xff\xfe\xfd")}, version=4
        )
        parsed = parse_frames(built, version=4)
        assert isinstance(parsed["PRIV"], UnknownFrame)
        assert parsed["PRIV"].raw == b"\xff\xfe\xfd"

    def test_stops_at_padding(self):
        built = build_frames({"TIT2": TextFrame("TIT2", "X")}, version=4)
        padded = built + b"\x00" * 20
        parsed = parse_frames(padded, version=4)
        assert list(parsed.keys()) == ["TIT2"]


class TestFrameRepr:
    def test_short_text_frame_shown_in_full(self):
        r = repr(TextFrame("TIT2", "Hello"))
        assert r == "TextFrame(frame_id='TIT2', text='Hello')"

    def test_class_name_is_shown(self):
        assert repr(TextFrame("TIT2", "Hi")).startswith("TextFrame(")
        assert repr(PictureFrame("APIC", "image/jpeg", 3, "", b"")).startswith(
            "PictureFrame("
        )

    def test_long_picture_data_is_truncated(self):
        frame = PictureFrame(
            frame_id="APIC",
            mime="image/jpeg",
            picture_type=3,
            description="cover",
            data=b"\xff\xd8\xff\xe0" + b"\x00" * 5_000,
        )
        r = repr(frame)
        # The full bytes blob never appears, but the short fields still do.
        assert "..." in r
        assert "frame_id='APIC'" in r
        assert "mime='image/jpeg'" in r
        assert "description='cover'" in r
        # No single field repr exceeds the limit + ellipsis length.
        # (50 chars of repr + 3 chars for "..." = 53 max for any field value)
        for piece in r.split(", "):
            value_repr = piece.split("=", 1)[-1].rstrip(")")
            assert len(value_repr) <= FIELD_REPR_LIMIT + 3

    def test_geob_short_data_not_truncated(self):
        frame = GeneralObjectFrame(
            frame_id="GEOB",
            mime="text/plain",
            filename="note.txt",
            description="note",
            data=b"hello",
        )
        r = repr(frame)
        assert "data=b'hello'" in r
        assert "..." not in r

    def test_geob_long_data_truncated(self):
        frame = GeneralObjectFrame(
            frame_id="GEOB",
            mime="application/octet-stream",
            filename="big.bin",
            description="big",
            data=b"x" * 500,
        )
        r = repr(frame)
        # Original 500-byte payload should not appear in full.
        assert "x" * 500 not in r
        assert "..." in r

    def test_unknown_frame_long_raw_truncated(self):
        frame = UnknownFrame("PRIV", b"\xff" * 200)
        r = repr(frame)
        assert "..." in r
        assert "frame_id='PRIV'" in r


def test_round_trip_multiple_frames():
    frames = {
        "TIT2": TextFrame("TIT2", "Song Title"),
        "TPE1": TextFrame("TPE1", "Artist Name"),
        "TALB": TextFrame("TALB", "Album Name"),
        "PRIV": UnknownFrame("PRIV", b"\xff\xd8\xff\xe0\x00\x10"),
    }
    built = build_frames(frames, version=4)
    parsed = parse_frames(built, version=4)

    assert len(parsed) == 4
    assert parsed["TIT2"].text == "Song Title"
    assert parsed["TPE1"].text == "Artist Name"
    assert parsed["TALB"].text == "Album Name"
    assert parsed["PRIV"].raw == b"\xff\xd8\xff\xe0\x00\x10"
