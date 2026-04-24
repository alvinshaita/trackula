from trackula.frame import (
    CommentFrame,
    GeneralObjectFrame,
    PictureFrame,
    TextFrame,
    UnknownFrame,
)
from trackula.tag import Tag


class TestEmptyTag:
    def test_default_frames(self):
        assert len(Tag().frames) == 0

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


class TestSummary:
    def test_empty_tag(self):
        assert Tag().summary() == []

    def test_text_frame_shown_in_full(self):
        t = Tag()
        t.frames["TIT2"] = TextFrame("TIT2", "Hello")
        assert t.summary() == [{"frame_id": "TIT2", "text": "Hello"}]

    def test_one_entry_per_frame_in_order(self):
        t = Tag()
        t.frames.add(TextFrame("TIT2", "Song"))
        t.frames.add(TextFrame("TPE1", "Artist"))
        t.frames.add(TextFrame("TALB", "Album"))
        ids = [entry["frame_id"] for entry in t.summary()]
        assert ids == ["TIT2", "TPE1", "TALB"]

    def test_multiple_frames_with_same_id_each_appear(self):
        t = Tag()
        t.frames.add(CommentFrame("COMM", "eng", "", "English note"))
        t.frames.add(CommentFrame("COMM", "spa", "", "Nota"))
        summary = t.summary()
        assert len(summary) == 2
        assert summary[0]["language"] == "eng"
        assert summary[1]["language"] == "spa"

    def test_picture_data_is_elided(self):
        t = Tag()
        t.frames["APIC"] = PictureFrame(
            frame_id="APIC",
            mime="image/jpeg",
            picture_type=3,
            description="cover",
            data=b"\xff\xd8" + b"\x00" * 10_000,
        )
        [entry] = t.summary()
        assert entry == {
            "frame_id": "APIC",
            "mime": "image/jpeg",
            "picture_type": 3,
            "description": "cover",
            "data": "...",
        }

    def test_geob_short_data_is_shown(self):
        t = Tag()
        t.frames["GEOB"] = GeneralObjectFrame(
            frame_id="GEOB",
            mime="text/plain",
            filename="note.txt",
            description="note",
            data=b"hello",
        )
        [entry] = t.summary()
        assert entry["data"] == b"hello"

    def test_geob_boundary_at_50_bytes_is_shown(self):
        t = Tag()
        payload = b"x" * 50
        t.frames["GEOB"] = GeneralObjectFrame(
            frame_id="GEOB",
            mime="application/octet-stream",
            filename="",
            description="",
            data=payload,
        )
        [entry] = t.summary()
        assert entry["data"] == payload

    def test_geob_long_data_is_elided(self):
        t = Tag()
        t.frames["GEOB"] = GeneralObjectFrame(
            frame_id="GEOB",
            mime="application/octet-stream",
            filename="big.bin",
            description="big",
            data=b"x" * 51,
        )
        [entry] = t.summary()
        assert entry == {
            "frame_id": "GEOB",
            "mime": "application/octet-stream",
            "filename": "big.bin",
            "description": "big",
            "data": "...",
        }

    def test_unknown_frame_raw_not_elided(self):
        # Only APIC + GEOB are special-cased. Other frames are shown as-is.
        t = Tag()
        t.frames["XYZZ"] = UnknownFrame("XYZZ", b"\x00\x01\x02")
        [entry] = t.summary()
        assert entry == {"frame_id": "XYZZ", "raw": b"\x00\x01\x02"}
