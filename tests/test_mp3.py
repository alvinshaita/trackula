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

        split = split_mp3(str(path))
        assert split.v2_tag[:3] == b"ID3"
        assert split.audio == FAKE_AUDIO
        assert split.v1_tag == b""

    def test_file_without_tag(self, tmp_path):
        path = tmp_path / "song.mp3"
        path.write_bytes(FAKE_AUDIO)

        split = split_mp3(str(path))
        assert split.v2_tag == b""
        assert split.audio == FAKE_AUDIO
        assert split.v1_tag == b""


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

    split = split_mp3(str(path))
    write_mp3(str(path), split.v2_tag, split.audio)

    split2 = split_mp3(str(path))
    assert split2.audio == FAKE_AUDIO
    assert split2.v2_tag == split.v2_tag
