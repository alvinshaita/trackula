import pytest

from trackula.errors import InvalidHeaderError
from trackula.id3.header import HEADER_SIZE, build_header, parse_header


class TestParseHeader:
    def test_valid_v24(self):
        # ID3 + version 4 + revision 0 + flags 0 + synchsafe size 100
        data = b"ID3" + b"\x04\x00" + b"\x00" + b"\x00\x00\x00\x64"
        result = parse_header(data)
        assert result["version"] == 4
        assert result["revision"] == 0
        assert result["flags"] == 0
        assert result["size"] == 100

    def test_valid_v23(self):
        data = b"ID3" + b"\x03\x00" + b"\x00" + b"\x00\x00\x00\x7f"
        result = parse_header(data)
        assert result["version"] == 3
        assert result["size"] == 127

    def test_short_data_raises(self):
        with pytest.raises(InvalidHeaderError, match="too short"):
            parse_header(b"ID3")

    def test_missing_identifier_raises(self):
        data = b"XXX" + b"\x04\x00" + b"\x00" + b"\x00\x00\x00\x00"
        with pytest.raises(InvalidHeaderError, match="identifier"):
            parse_header(data)


class TestBuildHeader:
    def test_default_v4(self):
        header = build_header(100)
        assert header[:3] == b"ID3"
        assert header[3] == 4
        assert header[4] == 0
        assert header[5] == 0
        assert header[6:10] == b"\x00\x00\x00\x64"

    def test_v23(self):
        header = build_header(100, version=3)
        assert header[3] == 3
        assert len(header) == HEADER_SIZE

    def test_size_is_synchsafe(self):
        # 128 in synchsafe is 0x00 0x00 0x01 0x00, not 0x00 0x00 0x00 0x80
        header = build_header(128)
        assert header[6:10] == b"\x00\x00\x01\x00"


def test_round_trip():
    built = build_header(1024, version=4)
    parsed = parse_header(built)
    assert parsed["version"] == 4
    assert parsed["size"] == 1024
