import pytest

from trackula.id3.encoding import decode_text, encode_text


class TestEncodeText:
    def test_latin1_prefix(self):
        assert encode_text("ABC", encoding=0) == b"\x00ABC"

    def test_utf16_prefix(self):
        encoded = encode_text("ABC", encoding=1)
        assert encoded[0] == 0x01

    def test_utf8_prefix(self):
        assert encode_text("ABC", encoding=3) == b"\x03ABC"

    def test_default_encoding_is_utf8(self):
        assert encode_text("ABC") == b"\x03ABC"


class TestDecodeText:
    def test_latin1(self):
        assert decode_text(b"\x00Hello") == "Hello"

    def test_utf8(self):
        assert decode_text(b"\x03Hello") == "Hello"

    def test_utf16(self):
        payload = "Hello".encode("utf-16")
        assert decode_text(b"\x01" + payload) == "Hello"

    def test_unknown_encoding_falls_back_to_latin1(self):
        assert decode_text(b"\x99Hello") == "Hello"


@pytest.mark.parametrize("encoding", [0, 1, 3])
@pytest.mark.parametrize("text", ["Hello", "", "with spaces", "123"])
def test_ascii_round_trip(text, encoding):
    assert decode_text(encode_text(text, encoding=encoding)) == text


@pytest.mark.parametrize("encoding", [1, 3])
def test_unicode_round_trip(encoding):
    text = "café ☕"
    assert decode_text(encode_text(text, encoding=encoding)) == text
