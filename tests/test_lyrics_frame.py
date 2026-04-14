from trackula.frame import LyricsFrame, SyncedLyricsEntry, SyncedLyricsFrame
from trackula.id3.builder import build_id3
from trackula.id3.frames import parse_frames
from trackula.id3.parser import parse_id3


class TestUnsyncedLyrics:
    def test_round_trip(self):
        original = LyricsFrame(
            frame_id="USLT",
            language="eng",
            description="",
            text="Row row row your boat\nGently down the stream",
        )
        built = build_id3({"USLT": original})
        parsed = parse_id3(built)["frames"]["USLT"]

        assert isinstance(parsed, LyricsFrame)
        assert parsed.language == "eng"
        assert parsed.description == ""
        assert parsed.text == "Row row row your boat\nGently down the stream"

    def test_non_english_language(self):
        original = LyricsFrame("USLT", "spa", "", "La vida es bella")
        built = build_id3({"USLT": original})
        parsed = parse_id3(built)["frames"]["USLT"]
        assert parsed.language == "spa"
        assert parsed.text == "La vida es bella"

    def test_unicode_text(self):
        original = LyricsFrame("USLT", "jpn", "", "桜の花びら\n風に舞う")
        built = build_id3({"USLT": original})
        parsed = parse_id3(built)["frames"]["USLT"]
        assert parsed.text == "桜の花びら\n風に舞う"

    def test_non_empty_description(self):
        original = LyricsFrame("USLT", "eng", "Verse 1", "First line")
        built = build_id3({"USLT": original})
        parsed = parse_id3(built)["frames"]["USLT"]
        assert parsed.description == "Verse 1"
        assert parsed.text == "First line"

    def test_routed_to_lyrics_parser(self):
        built = build_id3({"USLT": LyricsFrame("USLT", "eng", "", "x")})
        parsed = parse_frames(built[10:], version=4)
        assert isinstance(parsed["USLT"], LyricsFrame)


class TestSyncedLyrics:
    def test_round_trip_basic(self):
        entries = [
            SyncedLyricsEntry(text="Hello", timestamp=0),
            SyncedLyricsEntry(text="world", timestamp=1000),
        ]
        original = SyncedLyricsFrame(
            frame_id="SYLT",
            language="eng",
            timestamp_format=2,  # milliseconds
            content_type=1,  # lyrics
            description="",
            entries=entries,
        )
        built = build_id3({"SYLT": original})
        parsed = parse_id3(built)["frames"]["SYLT"]

        assert isinstance(parsed, SyncedLyricsFrame)
        assert parsed.language == "eng"
        assert parsed.timestamp_format == 2
        assert parsed.content_type == 1
        assert parsed.description == ""
        assert len(parsed.entries) == 2
        assert parsed.entries[0].text == "Hello"
        assert parsed.entries[0].timestamp == 0
        assert parsed.entries[1].text == "world"
        assert parsed.entries[1].timestamp == 1000

    def test_many_entries(self):
        entries = [
            SyncedLyricsEntry(text=f"Line {i}", timestamp=i * 500)
            for i in range(20)
        ]
        original = SyncedLyricsFrame(
            "SYLT", "eng", 2, 1, "Verse 1", entries
        )
        built = build_id3({"SYLT": original})
        parsed = parse_id3(built)["frames"]["SYLT"]
        assert len(parsed.entries) == 20
        for i, entry in enumerate(parsed.entries):
            assert entry.text == f"Line {i}"
            assert entry.timestamp == i * 500

    def test_empty_entries(self):
        original = SyncedLyricsFrame("SYLT", "eng", 2, 1, "", [])
        built = build_id3({"SYLT": original})
        parsed = parse_id3(built)["frames"]["SYLT"]
        assert len(parsed.entries) == 0

    def test_unicode_entry_text(self):
        entries = [
            SyncedLyricsEntry(text="日本語", timestamp=100),
            SyncedLyricsEntry(text="café", timestamp=200),
        ]
        original = SyncedLyricsFrame("SYLT", "mul", 2, 1, "", entries)
        built = build_id3({"SYLT": original})
        parsed = parse_id3(built)["frames"]["SYLT"]
        assert parsed.entries[0].text == "日本語"
        assert parsed.entries[1].text == "café"

    def test_large_timestamp(self):
        # 24-hour podcast ≈ 86_400_000 ms, well below 2**32 cap of 4294967295
        entries = [SyncedLyricsEntry(text="late", timestamp=86_400_000)]
        original = SyncedLyricsFrame("SYLT", "eng", 2, 1, "", entries)
        built = build_id3({"SYLT": original})
        parsed = parse_id3(built)["frames"]["SYLT"]
        assert parsed.entries[0].timestamp == 86_400_000
