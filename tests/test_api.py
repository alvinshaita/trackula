from trackula import AudioFile, Tag, read, write
from trackula.containers.mp3 import split_mp3
from trackula.frame import TextFrame
from trackula.id3.builder import build_id3
import pytest

FAKE_AUDIO = b"\xff\xfb" + b"\x00" * 200


def _seed(path, frames=None):
    path.write_bytes(build_id3(frames or {}) + FAKE_AUDIO)


class TestRead:
    def test_reads_existing_tag(self, tmp_path):
        path = tmp_path / "song.mp3"
        _seed(path, {"TIT2": TextFrame("TIT2", "Hello")})

        tag = read(str(path))
        assert isinstance(tag, Tag)
        assert tag.title == "Hello"

    def test_empty_file_returns_empty_tag(self, tmp_path):
        path = tmp_path / "song.mp3"
        path.write_bytes(FAKE_AUDIO)

        tag = read(str(path))
        assert isinstance(tag, Tag)
        assert len(tag.frames) == 0


class TestWrite:
    def test_writes_new_tag(self, tmp_path):
        path = tmp_path / "song.mp3"
        _seed(path)

        tag = Tag()
        tag.title = "New Title"
        write(str(path), tag)

        assert read(str(path)).title == "New Title"

    def test_preserves_audio(self, tmp_path):
        path = tmp_path / "song.mp3"
        _seed(path)

        tag = Tag()
        tag.title = "Whatever"
        write(str(path), tag)

        assert split_mp3(str(path)).audio == FAKE_AUDIO

    def test_replaces_existing_tag(self, tmp_path):
        path = tmp_path / "song.mp3"
        _seed(path, {"TIT2": TextFrame("TIT2", "Old")})

        tag = Tag()
        tag.title = "New"
        write(str(path), tag)

        assert read(str(path)).title == "New"


class TestAudioFile:
    def test_load(self, tmp_path):
        path = tmp_path / "song.mp3"
        _seed(path, {"TIT2": TextFrame("TIT2", "Loaded")})

        f = AudioFile(str(path))
        assert f.tag.title == "Loaded"
        assert f.path == str(path)

    def test_save_in_place(self, tmp_path):
        path = tmp_path / "song.mp3"
        _seed(path, {"TIT2": TextFrame("TIT2", "Old")})

        f = AudioFile(str(path))
        f.tag.title = "New"
        f.save()

        assert AudioFile(str(path)).tag.title == "New"

    def test_save_to_different_path(self, tmp_path):
        src = tmp_path / "src.mp3"
        dst = tmp_path / "dst.mp3"
        _seed(src, {"TIT2": TextFrame("TIT2", "Original")})

        AudioFile(str(src)).save(str(dst))

        assert dst.exists()
        assert AudioFile(str(dst)).tag.title == "Original"

    def test_save_to_different_path_preserves_audio(self, tmp_path):
        # regression guard: save(other) must use the source's audio bytes,
        # not whatever happens to exist at the destination.
        src = tmp_path / "src.mp3"
        dst = tmp_path / "dst.mp3"
        _seed(src, {"TIT2": TextFrame("TIT2", "Source")})

        AudioFile(str(src)).save(str(dst))

        assert split_mp3(str(dst)).audio == FAKE_AUDIO

    def test_repr(self, tmp_path):
        path = tmp_path / "song.mp3"
        _seed(path)
        f = AudioFile(str(path))
        assert str(path) in repr(f)
