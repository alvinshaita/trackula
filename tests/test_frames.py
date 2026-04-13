import pytest

from trackula.frame import TextFrame, UnknownFrame
from trackula.id3.frames import build_frame, build_frames, parse_frames


class TestBuildFrame:
    def test_text_frame_header(self):
        frame = TextFrame(frame_id="TIT2", text="Hello")
        result = build_frame(frame, version=4)
        assert result[:4] == b"TIT2"

    def test_unknown_frame_preserves_raw(self):
        frame = UnknownFrame(frame_id="APIC", raw=b"\xff\xd8\xff\xe0")
        result = build_frame(frame, version=4)
        assert result[:4] == b"APIC"
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
        assert parse_frames(b"", version=4) == {}

    def test_parse_text_frame(self):
        built = build_frames({"TIT2": TextFrame("TIT2", "Hello")}, version=4)
        parsed = parse_frames(built, version=4)
        assert "TIT2" in parsed
        assert isinstance(parsed["TIT2"], TextFrame)
        assert parsed["TIT2"].text == "Hello"
        assert parsed["TIT2"].frame_id == "TIT2"

    def test_parse_unknown_frame(self):
        built = build_frames(
            {"APIC": UnknownFrame("APIC", b"\xff\xfe\xfd")}, version=4
        )
        parsed = parse_frames(built, version=4)
        assert isinstance(parsed["APIC"], UnknownFrame)
        assert parsed["APIC"].raw == b"\xff\xfe\xfd"

    def test_stops_at_padding(self):
        built = build_frames({"TIT2": TextFrame("TIT2", "X")}, version=4)
        padded = built + b"\x00" * 20
        parsed = parse_frames(padded, version=4)
        assert list(parsed.keys()) == ["TIT2"]


def test_round_trip_multiple_frames():
    frames = {
        "TIT2": TextFrame("TIT2", "Song Title"),
        "TPE1": TextFrame("TPE1", "Artist Name"),
        "TALB": TextFrame("TALB", "Album Name"),
        "APIC": UnknownFrame("APIC", b"\xff\xd8\xff\xe0\x00\x10"),
    }
    built = build_frames(frames, version=4)
    parsed = parse_frames(built, version=4)

    assert len(parsed) == 4
    assert parsed["TIT2"].text == "Song Title"
    assert parsed["TPE1"].text == "Artist Name"
    assert parsed["TALB"].text == "Album Name"
    assert parsed["APIC"].raw == b"\xff\xd8\xff\xe0\x00\x10"
