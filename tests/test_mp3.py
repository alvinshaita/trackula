from trackula.containers.mp3 import split_mp3, write_mp3
from trackula.frame import TextFrame
from trackula.id3.builder import build_id3

FAKE_AUDIO = b"\xff\xfb" + b"\x00" * 200  # fake MPEG frame sync + padding


def _make_mp3_bytes(frames=None):
    return build_id3(frames or {}) + FAKE_AUDIO


class TestSplitMp3:
    def test_file_with_tag(self, tmp_path):
        path = tmp_path / "song.mp3"
        path.write_bytes(_make_mp3_bytes({"TIT2": TextFrame("TIT2", "Hello")}))

        tag_bytes, audio_bytes = split_mp3(str(path))
        assert tag_bytes[:3] == b"ID3"
        assert audio_bytes == FAKE_AUDIO

    def test_file_without_tag(self, tmp_path):
        path = tmp_path / "song.mp3"
        path.write_bytes(FAKE_AUDIO)

        tag_bytes, audio_bytes = split_mp3(str(path))
        assert tag_bytes == b""
        assert audio_bytes == FAKE_AUDIO


class TestWriteMp3:
    def test_concatenates_tag_and_audio(self, tmp_path):
        path = tmp_path / "out.mp3"
        write_mp3(str(path), b"HEAD", b"TAIL")
        assert path.read_bytes() == b"HEADTAIL"

    def test_overwrites_existing(self, tmp_path):
        path = tmp_path / "out.mp3"
        path.write_bytes(b"original content that should be replaced")
        write_mp3(str(path), b"new", b"data")
        assert path.read_bytes() == b"newdata"


def test_split_then_write_preserves_audio(tmp_path):
    path = tmp_path / "song.mp3"
    frames = {"TIT2": TextFrame("TIT2", "Round Trip")}
    path.write_bytes(_make_mp3_bytes(frames))

    tag_bytes, audio_bytes = split_mp3(str(path))
    write_mp3(str(path), tag_bytes, audio_bytes)

    tag_bytes2, audio_bytes2 = split_mp3(str(path))
    assert audio_bytes2 == FAKE_AUDIO
    assert tag_bytes2 == tag_bytes
