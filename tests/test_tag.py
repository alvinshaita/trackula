from trackula.frame import TextFrame, UnknownFrame
from trackula.tag import Tag


class TestEmptyTag:
    def test_default_frames(self):
        assert Tag().frames == {}

    def test_default_friendly_accessor(self):
        assert Tag().title is None

    def test_independent_instances(self):
        # regression guard against shared mutable default
        t1 = Tag()
        t1.title = "X"
        t2 = Tag()
        assert t2.title is None


class TestFriendlyAccessors:
    def test_set_string_wraps_into_text_frame(self):
        t = Tag()
        t.title = "Hello"
        assert isinstance(t.frames["TIT2"], TextFrame)
        assert t.frames["TIT2"].text == "Hello"
        assert t.frames["TIT2"].frame_id == "TIT2"

    def test_get_unwraps_text_frame(self):
        t = Tag()
        t.frames["TIT2"] = TextFrame("TIT2", "Hello")
        assert t.title == "Hello"

    def test_frame_id_alias_shares_storage(self):
        t = Tag()
        t.TIT2 = "Hello"
        assert t.title == "Hello"

    def test_multiple_friendly_names(self):
        t = Tag()
        t.title = "Title"
        t.artist = "Artist"
        t.album = "Album"
        assert t.frames["TIT2"].text == "Title"
        assert t.frames["TPE1"].text == "Artist"
        assert t.frames["TALB"].text == "Album"


class TestNonTextAccessors:
    def test_picture_accepts_frame(self):
        t = Tag()
        frame = UnknownFrame("APIC", b"\x00\x01")
        t.picture = frame
        assert t.picture is frame

    def test_picture_get_returns_frame_not_string(self):
        t = Tag()
        t.frames["APIC"] = UnknownFrame("APIC", b"\x00\x01")
        assert isinstance(t.picture, UnknownFrame)


class TestGetSet:
    def test_get_method(self):
        t = Tag()
        t.frames["TIT2"] = TextFrame("TIT2", "X")
        assert t.get("TIT2").text == "X"

    def test_set_method(self):
        t = Tag()
        t.set("TIT2", TextFrame("TIT2", "X"))
        assert t.frames["TIT2"].text == "X"

    def test_get_missing_returns_none(self):
        assert Tag().get("TIT2") is None


class TestTagConstructor:
    def test_with_initial_frames(self):
        frames = {"TIT2": TextFrame("TIT2", "Hello")}
        t = Tag(frames)
        assert t.title == "Hello"
