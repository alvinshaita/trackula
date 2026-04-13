from trackula.frame import CommentFrame
from trackula.id3.builder import build_id3
from trackula.id3.frames import parse_frames
from trackula.id3.parser import parse_id3


def _make_comment(language="eng", desc="", text="Hello world"):
    return CommentFrame(
        frame_id="COMM",
        language=language,
        description=desc,
        text=text,
    )


class TestRoundTrip:
    def test_defaults(self):
        original = _make_comment()
        built = build_id3({"COMM": original})
        parsed = parse_id3(built)["frames"]["COMM"]

        assert isinstance(parsed, CommentFrame)
        assert parsed.language == "eng"
        assert parsed.description == ""
        assert parsed.text == "Hello world"

    def test_non_english_language(self):
        original = _make_comment(language="spa", text="Hola mundo")
        built = build_id3({"COMM": original})
        parsed = parse_id3(built)["frames"]["COMM"]
        assert parsed.language == "spa"
        assert parsed.text == "Hola mundo"

    def test_unicode_text(self):
        original = _make_comment(text="日本語 コメント")
        built = build_id3({"COMM": original})
        parsed = parse_id3(built)["frames"]["COMM"]
        assert parsed.text == "日本語 コメント"

    def test_non_empty_description(self):
        original = _make_comment(desc="Mood", text="Chill")
        built = build_id3({"COMM": original})
        parsed = parse_id3(built)["frames"]["COMM"]
        assert parsed.description == "Mood"
        assert parsed.text == "Chill"

    def test_description_and_text_both_unicode(self):
        original = _make_comment(desc="Título", text="El álbum de año")
        built = build_id3({"COMM": original})
        parsed = parse_id3(built)["frames"]["COMM"]
        assert parsed.description == "Título"
        assert parsed.text == "El álbum de año"


def test_language_is_truncated_to_three_chars():
    # builder should clamp the language field to the 3-byte spec requirement
    original = _make_comment(language="english")
    built = build_id3({"COMM": original})
    parsed = parse_id3(built)["frames"]["COMM"]
    assert parsed.language == "eng"


def test_parses_via_frames_dispatch():
    built = build_id3({"COMM": _make_comment()})
    parsed = parse_frames(built[10:], version=4)
    assert isinstance(parsed["COMM"], CommentFrame)
