from trackula.frame import UrlFrame, UserUrlFrame
from trackula.id3.builder import build_id3
from trackula.id3.frames import parse_frames
from trackula.id3.parser import parse_id3


class TestUrlFrame:
    def test_round_trip_woar(self):
        original = UrlFrame(frame_id="WOAR", url="https://artist.example.com")
        built = build_id3({"WOAR": original})
        parsed = parse_id3(built)["frames"]["WOAR"]

        assert isinstance(parsed, UrlFrame)
        assert parsed.frame_id == "WOAR"
        assert parsed.url == "https://artist.example.com"

    def test_round_trip_wcop(self):
        original = UrlFrame(frame_id="WCOP", url="https://copyright.example.com")
        built = build_id3({"WCOP": original})
        parsed = parse_id3(built)["frames"]["WCOP"]
        assert parsed.url == "https://copyright.example.com"

    def test_dispatched_via_prefix_rule(self):
        # WCOM isn't in the exact registry; the W??? prefix rule routes it.
        built = build_id3({"WCOM": UrlFrame("WCOM", "https://shop.example.com")})
        parsed = parse_frames(built[10:], version=4)
        assert isinstance(parsed["WCOM"], UrlFrame)


class TestUserUrlFrame:
    def test_round_trip(self):
        original = UserUrlFrame(
            frame_id="WXXX",
            description="Bandcamp",
            url="https://band.bandcamp.com",
        )
        built = build_id3({"WXXX": original})
        parsed = parse_id3(built)["frames"]["WXXX"]

        assert isinstance(parsed, UserUrlFrame)
        assert parsed.frame_id == "WXXX"
        assert parsed.description == "Bandcamp"
        assert parsed.url == "https://band.bandcamp.com"

    def test_empty_description(self):
        original = UserUrlFrame(frame_id="WXXX", description="", url="https://example.com")
        built = build_id3({"WXXX": original})
        parsed = parse_id3(built)["frames"]["WXXX"]
        assert parsed.description == ""
        assert parsed.url == "https://example.com"

    def test_unicode_description(self):
        original = UserUrlFrame(
            frame_id="WXXX",
            description="Página oficial",
            url="https://oficial.example.es",
        )
        built = build_id3({"WXXX": original})
        parsed = parse_id3(built)["frames"]["WXXX"]
        assert parsed.description == "Página oficial"
        assert parsed.url == "https://oficial.example.es"

    def test_wxxx_not_caught_by_prefix_rule(self):
        # WXXX must route to UserUrlFrame, not UrlFrame
        built = build_id3({"WXXX": UserUrlFrame("WXXX", "x", "https://e.com")})
        parsed = parse_frames(built[10:], version=4)
        assert isinstance(parsed["WXXX"], UserUrlFrame)
