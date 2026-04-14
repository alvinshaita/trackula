from trackula.frame import (
    PlayCountFrame,
    PopularimeterFrame,
    UniqueFileIdentifierFrame,
)
from trackula.id3.builder import build_id3
from trackula.id3.frames import parse_frames
from trackula.id3.parser import parse_id3


class TestPopularimeter:
    def test_round_trip(self):
        original = PopularimeterFrame(
            frame_id="POPM",
            email="user@example.com",
            rating=200,
            counter=42,
        )
        built = build_id3({"POPM": original})
        parsed = parse_id3(built)["frames"]["POPM"]

        assert isinstance(parsed, PopularimeterFrame)
        assert parsed.email == "user@example.com"
        assert parsed.rating == 200
        assert parsed.counter == 42

    def test_empty_email(self):
        original = PopularimeterFrame("POPM", "", 0, 0)
        built = build_id3({"POPM": original})
        parsed = parse_id3(built)["frames"]["POPM"]
        assert parsed.email == ""
        assert parsed.rating == 0
        assert parsed.counter == 0

    def test_max_rating(self):
        original = PopularimeterFrame("POPM", "wmp@windows.local", 255, 1)
        built = build_id3({"POPM": original})
        parsed = parse_id3(built)["frames"]["POPM"]
        assert parsed.rating == 255

    def test_large_counter_extends_past_32_bits(self):
        # 2**33 needs 5 bytes; builder must extend the counter accordingly.
        original = PopularimeterFrame("POPM", "u@e.com", 128, 2**33)
        built = build_id3({"POPM": original})
        parsed = parse_id3(built)["frames"]["POPM"]
        assert parsed.counter == 2**33

    def test_routed_to_popm_parser(self):
        built = build_id3({"POPM": PopularimeterFrame("POPM", "u@e.com", 1, 1)})
        parsed = parse_frames(built[10:], version=4)
        assert isinstance(parsed["POPM"], PopularimeterFrame)


class TestUFID:
    def test_round_trip(self):
        original = UniqueFileIdentifierFrame(
            frame_id="UFID",
            owner="http://musicbrainz.org",
            identifier=b"abc-123-def-456",
        )
        built = build_id3({"UFID": original})
        parsed = parse_id3(built)["frames"]["UFID"]

        assert isinstance(parsed, UniqueFileIdentifierFrame)
        assert parsed.owner == "http://musicbrainz.org"
        assert parsed.identifier == b"abc-123-def-456"

    def test_binary_identifier(self):
        original = UniqueFileIdentifierFrame(
            "UFID", "owner", b"\x00\x01\x02\xff\xfe"
        )
        built = build_id3({"UFID": original})
        parsed = parse_id3(built)["frames"]["UFID"]
        assert parsed.identifier == b"\x00\x01\x02\xff\xfe"

    def test_empty_identifier(self):
        original = UniqueFileIdentifierFrame("UFID", "owner", b"")
        built = build_id3({"UFID": original})
        parsed = parse_id3(built)["frames"]["UFID"]
        assert parsed.identifier == b""


class TestPlayCount:
    def test_round_trip(self):
        original = PlayCountFrame(frame_id="PCNT", count=42)
        built = build_id3({"PCNT": original})
        parsed = parse_id3(built)["frames"]["PCNT"]

        assert isinstance(parsed, PlayCountFrame)
        assert parsed.count == 42

    def test_zero(self):
        original = PlayCountFrame("PCNT", 0)
        built = build_id3({"PCNT": original})
        parsed = parse_id3(built)["frames"]["PCNT"]
        assert parsed.count == 0

    def test_large_count_extends(self):
        original = PlayCountFrame("PCNT", 2**35)
        built = build_id3({"PCNT": original})
        parsed = parse_id3(built)["frames"]["PCNT"]
        assert parsed.count == 2**35

    def test_max_32_bit(self):
        original = PlayCountFrame("PCNT", 2**32 - 1)
        built = build_id3({"PCNT": original})
        parsed = parse_id3(built)["frames"]["PCNT"]
        assert parsed.count == 2**32 - 1
