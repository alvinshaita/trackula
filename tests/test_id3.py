import pytest

from trackula.errors import InvalidHeaderError
from trackula.frame import TextFrame, UnknownFrame
from trackula.id3.builder import build_id3
from trackula.id3.parser import parse_id3


def test_round_trip_empty():
    built = build_id3({})
    parsed = parse_id3(built)
    assert parsed["frames"] == {}
    assert parsed["header"]["version"] == 4


def test_round_trip_single_text_frame():
    frames = {"TIT2": TextFrame("TIT2", "Title")}
    built = build_id3(frames)
    parsed = parse_id3(built)
    assert parsed["frames"]["TIT2"].text == "Title"


def test_round_trip_mixed_frames():
    frames = {
        "TIT2": TextFrame("TIT2", "Title"),
        "TPE1": TextFrame("TPE1", "Artist"),
        "TALB": TextFrame("TALB", "Album"),
        "APIC": UnknownFrame("APIC", b"\x89PNG\r\n\x1a\n"),
    }
    built = build_id3(frames)
    parsed = parse_id3(built)

    assert parsed["frames"]["TIT2"].text == "Title"
    assert parsed["frames"]["TPE1"].text == "Artist"
    assert parsed["frames"]["TALB"].text == "Album"
    assert parsed["frames"]["APIC"].raw == b"\x89PNG\r\n\x1a\n"


def test_bad_identifier_raises():
    bad = b"XXX" + b"\x04\x00\x00" + b"\x00\x00\x00\x00"
    with pytest.raises(InvalidHeaderError, match="identifier"):
        parse_id3(bad)


def test_short_data_raises():
    with pytest.raises(InvalidHeaderError, match="too short"):
        parse_id3(b"ID3")
