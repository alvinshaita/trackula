from trackula import AudioFile, Tag, read, write
from trackula.containers.mp3 import parse_v1_tag, split_mp3
from trackula.frame import TextFrame
from trackula.id3.builder import build_id3

FAKE_AUDIO = b"\xff\xfb" + b"\x00" * 200


def _make_v1_tag(
    title: str = "",
    artist: str = "",
    album: str = "",
    year: str = "",
    comment: str = "",
    track: int = None,
    genre: int = 0xFF,
) -> bytes:
    """Assemble a valid 128-byte ID3v1 / v1.1 tag."""

    def field(value: str, length: int) -> bytes:
        return value.encode("latin1")[:length].ljust(length, b"\x00")

    tag = b"TAG"
    tag += field(title, 30)
    tag += field(artist, 30)
    tag += field(album, 30)
    tag += field(year, 4)
    if track is not None:
        tag += field(comment, 28) + b"\x00" + bytes([track])
    else:
        tag += field(comment, 30)
    tag += bytes([genre])
    assert len(tag) == 128
    return tag


class TestParseV1Tag:
    def test_minimal(self):
        v1 = _make_v1_tag(title="Song", artist="Artist")
        fc = parse_v1_tag(v1)
        assert fc["TIT2"].text == "Song"
        assert fc["TPE1"].text == "Artist"

    def test_all_fields_v11(self):
        v1 = _make_v1_tag(
            title="Song Title",
            artist="Artist Name",
            album="Album Name",
            year="2024",
            comment="Nice song",
            track=3,
            genre=17,  # Rock
        )
        fc = parse_v1_tag(v1)
        assert fc["TIT2"].text == "Song Title"
        assert fc["TPE1"].text == "Artist Name"
        assert fc["TALB"].text == "Album Name"
        assert fc["TYER"].text == "2024"
        assert fc["COMM"].text == "Nice song"
        assert fc["COMM"].language == "eng"
        assert fc["COMM"].description == ""
        assert fc["TRCK"].text == "3"
        assert fc["TCON"].text == "Rock"

    def test_v10_without_track(self):
        v1 = _make_v1_tag(title="x", comment="just a regular comment")
        fc = parse_v1_tag(v1)
        assert "TRCK" not in fc
        assert fc["COMM"].text == "just a regular comment"

    def test_genre_out_of_range(self):
        v1 = _make_v1_tag(title="x", genre=200)  # beyond the 80 standard entries
        fc = parse_v1_tag(v1)
        assert "TCON" not in fc

    def test_genre_0_is_blues(self):
        v1 = _make_v1_tag(title="x", genre=0)
        fc = parse_v1_tag(v1)
        assert fc["TCON"].text == "Blues"

    def test_genre_79_is_hard_rock(self):
        # Last entry in the standard spec list.
        v1 = _make_v1_tag(title="x", genre=79)
        fc = parse_v1_tag(v1)
        assert fc["TCON"].text == "Hard Rock"

    def test_null_padding_stripped(self):
        v1 = _make_v1_tag(title="Short")
        fc = parse_v1_tag(v1)
        assert fc["TIT2"].text == "Short"

    def test_empty_fields_skipped(self):
        v1 = _make_v1_tag()
        fc = parse_v1_tag(v1)
        assert len(fc) == 0

    def test_latin1_accented_chars(self):
        v1 = _make_v1_tag(artist="Björk")
        fc = parse_v1_tag(v1)
        assert fc["TPE1"].text == "Björk"

    def test_not_a_v1_tag_returns_empty(self):
        fc = parse_v1_tag(b"NOT" + b"\x00" * 125)
        assert len(fc) == 0

    def test_wrong_size_returns_empty(self):
        fc = parse_v1_tag(b"TAG" + b"\x00" * 10)
        assert len(fc) == 0

    def test_empty_bytes_returns_empty(self):
        assert len(parse_v1_tag(b"")) == 0


class TestSplitMp3WithV1:
    def test_only_v1(self, tmp_path):
        path = tmp_path / "song.mp3"
        v1 = _make_v1_tag(title="V1 Only", artist="Old Tagger")
        path.write_bytes(FAKE_AUDIO + v1)

        split = split_mp3(str(path))
        assert split.v2_tag == b""
        assert split.audio == FAKE_AUDIO
        assert split.v1_tag == v1

    def test_only_v2(self, tmp_path):
        path = tmp_path / "song.mp3"
        v2 = build_id3({"TIT2": TextFrame("TIT2", "V2 Only")})
        path.write_bytes(v2 + FAKE_AUDIO)

        split = split_mp3(str(path))
        assert split.v2_tag == v2
        assert split.audio == FAKE_AUDIO
        assert split.v1_tag == b""

    def test_both_v1_and_v2(self, tmp_path):
        path = tmp_path / "song.mp3"
        v2 = build_id3({"TIT2": TextFrame("TIT2", "V2")})
        v1 = _make_v1_tag(title="V1")
        path.write_bytes(v2 + FAKE_AUDIO + v1)

        split = split_mp3(str(path))
        assert split.v2_tag == v2
        assert split.audio == FAKE_AUDIO
        assert split.v1_tag == v1

    def test_neither_tag(self, tmp_path):
        path = tmp_path / "song.mp3"
        path.write_bytes(FAKE_AUDIO)

        split = split_mp3(str(path))
        assert split.v2_tag == b""
        assert split.audio == FAKE_AUDIO
        assert split.v1_tag == b""

    def test_file_smaller_than_128_bytes(self, tmp_path):
        # A tiny file shouldn't be misread as a v1 tag.
        path = tmp_path / "tiny.mp3"
        path.write_bytes(b"\xff\xfb\x00\x00")  # 4 bytes

        split = split_mp3(str(path))
        assert split.v1_tag == b""
        assert split.audio == b"\xff\xfb\x00\x00"

    def test_audio_bytes_happening_to_end_in_TAG(self, tmp_path):
        # If the last 128 bytes don't start with "TAG" we should NOT treat
        # them as a v1 tag even if "TAG" appears somewhere else.
        path = tmp_path / "song.mp3"
        audio = b"\xff\xfb" + b"TAG" + b"\x00" * 200
        path.write_bytes(audio)

        split = split_mp3(str(path))
        assert split.v1_tag == b""


class TestReadFallback:
    def test_reads_v1_when_no_v2(self, tmp_path):
        path = tmp_path / "song.mp3"
        v1 = _make_v1_tag(title="V1 Title", artist="V1 Artist", genre=17)
        path.write_bytes(FAKE_AUDIO + v1)

        tag = read(str(path))
        assert tag.title == "V1 Title"
        assert tag.artist == "V1 Artist"
        assert tag.genre == "Rock"

    def test_v2_preferred_over_v1(self, tmp_path):
        # Real files sometimes have both. trackula picks v2, which is
        # richer and what every modern tagger produces.
        path = tmp_path / "song.mp3"
        v2 = build_id3({"TIT2": TextFrame("TIT2", "V2 Title")})
        v1 = _make_v1_tag(title="V1 Title")
        path.write_bytes(v2 + FAKE_AUDIO + v1)

        tag = read(str(path))
        assert tag.title == "V2 Title"

    def test_no_tags_returns_empty(self, tmp_path):
        path = tmp_path / "song.mp3"
        path.write_bytes(FAKE_AUDIO)
        assert len(read(str(path)).frames) == 0


class TestWriteDropsV1:
    def test_write_strips_existing_v1_footer(self, tmp_path):
        path = tmp_path / "song.mp3"
        v2 = build_id3({"TIT2": TextFrame("TIT2", "Original")})
        v1 = _make_v1_tag(title="V1 Title")
        path.write_bytes(v2 + FAKE_AUDIO + v1)

        tag = read(str(path))
        tag.title = "Modified"
        write(str(path), tag)

        split = split_mp3(str(path))
        assert split.v1_tag == b""
        assert split.audio == FAKE_AUDIO
        assert read(str(path)).title == "Modified"


class TestAudioFileFallback:
    def test_loads_from_v1(self, tmp_path):
        path = tmp_path / "song.mp3"
        v1 = _make_v1_tag(title="Loaded From V1", year="1999")
        path.write_bytes(FAKE_AUDIO + v1)

        f = AudioFile(str(path))
        assert f.tag.title == "Loaded From V1"
        assert f.tag.year == "1999"

    def test_save_migrates_v1_to_v2(self, tmp_path):
        path = tmp_path / "song.mp3"
        v1 = _make_v1_tag(title="Old Title")
        path.write_bytes(FAKE_AUDIO + v1)

        f = AudioFile(str(path))
        f.tag.title = "New Title"
        f.save()

        # The file should now be v2-only — no v1 footer.
        split = split_mp3(str(path))
        assert split.v1_tag == b""
        assert split.v2_tag[:3] == b"ID3"
        assert AudioFile(str(path)).tag.title == "New Title"

    def test_save_audio_integrity_with_v1_source(self, tmp_path):
        # Regression: AudioFile must store the pure audio (v1-stripped) so
        # rewriting doesn't double up the v1 footer or corrupt audio bytes.
        path = tmp_path / "song.mp3"
        v1 = _make_v1_tag(title="Old")
        path.write_bytes(FAKE_AUDIO + v1)

        f = AudioFile(str(path))
        f.save()

        assert split_mp3(str(path)).audio == FAKE_AUDIO
