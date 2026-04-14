from trackula.frame import UserTextFrame
from trackula.id3.builder import build_id3
from trackula.id3.frames import parse_frames
from trackula.id3.parser import parse_id3


def _make(description="musicbrainz_trackid", text="abc-123-def-456"):
    return UserTextFrame(
        frame_id="TXXX",
        description=description,
        text=text,
    )


class TestRoundTrip:
    def test_basic(self):
        original = _make()
        built = build_id3({"TXXX": original})
        parsed = parse_id3(built)["frames"]["TXXX"]

        assert isinstance(parsed, UserTextFrame)
        assert parsed.frame_id == "TXXX"
        assert parsed.description == "musicbrainz_trackid"
        assert parsed.text == "abc-123-def-456"

    def test_empty_description(self):
        original = _make(description="", text="value")
        built = build_id3({"TXXX": original})
        parsed = parse_id3(built)["frames"]["TXXX"]
        assert parsed.description == ""
        assert parsed.text == "value"

    def test_unicode_description_and_text(self):
        original = _make(description="Título", text="Canción — álbum")
        built = build_id3({"TXXX": original})
        parsed = parse_id3(built)["frames"]["TXXX"]
        assert parsed.description == "Título"
        assert parsed.text == "Canción — álbum"

    def test_replaygain_style(self):
        # One common real-world usage: ReplayGain values
        original = _make(description="replaygain_track_gain", text="-7.42 dB")
        built = build_id3({"TXXX": original})
        parsed = parse_id3(built)["frames"]["TXXX"]
        assert parsed.description == "replaygain_track_gain"
        assert parsed.text == "-7.42 dB"


def test_routed_to_user_text_parser_not_text_parser():
    # TXXX must route to parse_user_text, not parse_text — the latter would
    # treat the whole body as a single text blob and include the null
    # terminator in the decoded string.
    built = build_id3({"TXXX": _make()})
    parsed = parse_frames(built[10:], version=4)
    assert isinstance(parsed["TXXX"], UserTextFrame)
