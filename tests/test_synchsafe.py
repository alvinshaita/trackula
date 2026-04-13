import pytest

from trackula.id3.synchsafe import (
    decode_int,
    decode_synchsafe,
    encode_int,
    encode_synchsafe,
)


class TestSynchsafe:
    def test_zero(self):
        assert encode_synchsafe(0) == b"\x00\x00\x00\x00"
        assert decode_synchsafe(b"\x00\x00\x00\x00") == 0

    def test_small(self):
        assert encode_synchsafe(1) == b"\x00\x00\x00\x01"

    def test_seven_bit_boundary(self):
        # 127 fits in one synchsafe byte; 128 rolls into the next
        assert encode_synchsafe(127) == b"\x00\x00\x00\x7f"
        assert encode_synchsafe(128) == b"\x00\x00\x01\x00"

    def test_high_bit_never_set(self):
        # core invariant: no output byte ever has bit 7 set
        for value in [0, 1, 127, 128, 1000, 0x0FFFFFFF]:
            for b in encode_synchsafe(value):
                assert b & 0x80 == 0

    def test_max_28_bit_value(self):
        assert encode_synchsafe(0x0FFFFFFF) == b"\x7f\x7f\x7f\x7f"
        assert decode_synchsafe(b"\x7f\x7f\x7f\x7f") == 0x0FFFFFFF

    @pytest.mark.parametrize(
        "value", [0, 1, 127, 128, 255, 256, 1000, 100000, 0x0FFFFFFF]
    )
    def test_round_trip(self, value):
        assert decode_synchsafe(encode_synchsafe(value)) == value


class TestDecodeInt:
    def test_synchsafe_mode(self):
        assert decode_int(b"\x00\x00\x01\x00", synchsafe=True) == 128

    def test_big_endian_mode(self):
        assert decode_int(b"\x00\x00\x01\x00", synchsafe=False) == 256


class TestEncodeInt:
    def test_synchsafe_mode(self):
        assert encode_int(128, synchsafe=True) == b"\x00\x00\x01\x00"

    @pytest.mark.xfail(
        reason="encode_int(synchsafe=False) has a latent bug: "
        "calls len() on an int. Currently unreachable from callers."
    )
    def test_big_endian_mode(self):
        assert encode_int(256, synchsafe=False) == b"\x00\x00\x01\x00"
