import pytest

from trackula.frame import (
    CommentFrame,
    FrameCollection,
    PictureFrame,
    TextFrame,
    UnknownFrame,
)
from trackula.id3.builder import build_id3
from trackula.id3.parser import parse_id3


def _text(fid, value):
    return TextFrame(frame_id=fid, text=value)


def _comm(lang, desc, text):
    return CommentFrame(frame_id="COMM", language=lang, description=desc, text=text)


def _pic(mime, desc, data):
    return PictureFrame(
        frame_id="APIC", mime=mime, picture_type=3, description=desc, data=data
    )


class TestEmpty:
    def test_default_len(self):
        assert len(FrameCollection()) == 0

    def test_default_list(self):
        assert list(FrameCollection()) == []

    def test_get_missing_returns_none(self):
        assert FrameCollection().get("TIT2") is None

    def test_getitem_missing_raises(self):
        with pytest.raises(KeyError):
            FrameCollection()["TIT2"]

    def test_delitem_missing_raises(self):
        with pytest.raises(KeyError):
            del FrameCollection()["TIT2"]


class TestSingleFrameOperations:
    def test_setitem_getitem(self):
        fc = FrameCollection()
        fc["TIT2"] = _text("TIT2", "Hello")
        assert fc["TIT2"].text == "Hello"

    def test_setitem_replaces_existing(self):
        fc = FrameCollection([_text("TIT2", "Old")])
        fc["TIT2"] = _text("TIT2", "New")
        assert len(fc) == 1
        assert fc["TIT2"].text == "New"

    def test_delitem_removes(self):
        fc = FrameCollection([_text("TIT2", "x")])
        del fc["TIT2"]
        assert "TIT2" not in fc
        assert len(fc) == 0

    def test_contains(self):
        fc = FrameCollection([_text("TIT2", "x")])
        assert "TIT2" in fc
        assert "TPE1" not in fc


class TestMultiFrameOperations:
    def test_add_allows_duplicates(self):
        fc = FrameCollection()
        fc.add(_comm("eng", "", "English note"))
        fc.add(_comm("spa", "", "Nota española"))
        fc.add(_comm("fra", "", "Note française"))
        assert len(fc) == 3

    def test_getitem_returns_first_match(self):
        fc = FrameCollection()
        fc.add(_comm("eng", "", "first"))
        fc.add(_comm("spa", "", "second"))
        assert fc["COMM"].text == "first"

    def test_get_all_returns_all_matches(self):
        fc = FrameCollection()
        fc.add(_comm("eng", "", "first"))
        fc.add(_comm("spa", "", "second"))
        fc.add(_comm("fra", "", "third"))
        all_comms = fc.get_all("COMM")
        assert len(all_comms) == 3
        assert [c.text for c in all_comms] == ["first", "second", "third"]

    def test_get_all_preserves_insertion_order(self):
        fc = FrameCollection()
        fc.add(_comm("eng", "desc1", "A"))
        fc.add(_comm("eng", "desc2", "B"))
        fc.add(_comm("eng", "desc3", "C"))
        descs = [c.description for c in fc.get_all("COMM")]
        assert descs == ["desc1", "desc2", "desc3"]

    def test_setitem_replaces_all_duplicates(self):
        fc = FrameCollection()
        fc.add(_comm("eng", "", "first"))
        fc.add(_comm("spa", "", "second"))
        fc["COMM"] = _comm("fra", "", "only one")
        assert len(fc) == 1
        assert fc["COMM"].text == "only one"

    def test_delitem_removes_all_duplicates(self):
        fc = FrameCollection()
        fc.add(_comm("eng", "", "first"))
        fc.add(_comm("spa", "", "second"))
        fc.add(_text("TIT2", "keep me"))
        del fc["COMM"]
        assert len(fc) == 1
        assert fc["TIT2"].text == "keep me"

    def test_remove_all_returns_count(self):
        fc = FrameCollection()
        fc.add(_comm("eng", "", "first"))
        fc.add(_comm("spa", "", "second"))
        fc.add(_text("TIT2", "keep me"))
        removed = fc.remove_all("COMM")
        assert removed == 2
        assert len(fc) == 1

    def test_get_all_missing_returns_empty(self):
        assert FrameCollection().get_all("COMM") == []


class TestIterationAndViews:
    def test_iter_yields_all_frames(self):
        fc = FrameCollection()
        a = _text("TIT2", "x")
        b = _comm("eng", "", "first")
        c = _comm("spa", "", "second")
        fc.add(a)
        fc.add(b)
        fc.add(c)
        assert list(fc) == [a, b, c]

    def test_len_counts_total_frames(self):
        fc = FrameCollection()
        fc.add(_comm("eng", "", "a"))
        fc.add(_comm("spa", "", "b"))
        assert len(fc) == 2

    def test_frame_ids_unique_first_occurrence_order(self):
        fc = FrameCollection()
        fc.add(_text("TIT2", "x"))
        fc.add(_comm("eng", "", "a"))
        fc.add(_comm("spa", "", "b"))
        fc.add(_text("TPE1", "y"))
        assert fc.frame_ids() == ["TIT2", "COMM", "TPE1"]

    def test_keys_alias_of_frame_ids(self):
        fc = FrameCollection([_text("TIT2", "x"), _text("TPE1", "y")])
        assert fc.keys() == fc.frame_ids()

    def test_values_includes_duplicates(self):
        fc = FrameCollection()
        fc.add(_comm("eng", "", "a"))
        fc.add(_comm("spa", "", "b"))
        assert len(fc.values()) == 2

    def test_items_one_tuple_per_frame(self):
        fc = FrameCollection()
        fc.add(_text("TIT2", "x"))
        fc.add(_comm("eng", "", "a"))
        fc.add(_comm("spa", "", "b"))
        items = fc.items()
        assert len(items) == 3
        assert items[0] == ("TIT2", fc["TIT2"])
        assert [fid for fid, _ in items[1:]] == ["COMM", "COMM"]


class TestClearAndEq:
    def test_clear(self):
        fc = FrameCollection([_text("TIT2", "x"), _text("TPE1", "y")])
        fc.clear()
        assert len(fc) == 0

    def test_eq_empty(self):
        assert FrameCollection() == FrameCollection()
        assert FrameCollection() == []

    def test_eq_same_contents(self):
        a = FrameCollection([_text("TIT2", "x")])
        b = FrameCollection([_text("TIT2", "x")])
        assert a == b

    def test_neq_different_order(self):
        a = FrameCollection([_text("TIT2", "x"), _text("TPE1", "y")])
        b = FrameCollection([_text("TPE1", "y"), _text("TIT2", "x")])
        assert a != b

    def test_repr_includes_frames(self):
        fc = FrameCollection([_text("TIT2", "x")])
        assert "TIT2" in repr(fc)


class TestMultiFrameRoundTrip:
    def test_multiple_comm_frames_preserved(self):
        fc = FrameCollection()
        fc.add(_comm("eng", "Mood", "Chill"))
        fc.add(_comm("spa", "Estado", "Tranquilo"))
        fc.add(_comm("eng", "Note", "Recorded live"))

        built = build_id3(fc)
        parsed = parse_id3(built)["frames"]

        comms = parsed.get_all("COMM")
        assert len(comms) == 3
        assert (comms[0].language, comms[0].description, comms[0].text) == ("eng", "Mood", "Chill")
        assert (comms[1].language, comms[1].description, comms[1].text) == ("spa", "Estado", "Tranquilo")
        assert (comms[2].language, comms[2].description, comms[2].text) == ("eng", "Note", "Recorded live")

    def test_multiple_pictures_preserved(self):
        # A file can carry both a front cover and a back cover.
        front = PictureFrame("APIC", "image/jpeg", 3, "front", b"\xff\xd8\xff\xe0front")
        back = PictureFrame("APIC", "image/png", 4, "back", b"\x89PNGback")

        fc = FrameCollection()
        fc.add(front)
        fc.add(back)

        built = build_id3(fc)
        parsed = parse_id3(built)["frames"]

        pics = parsed.get_all("APIC")
        assert len(pics) == 2
        assert pics[0].description == "front"
        assert pics[0].picture_type == 3
        assert pics[1].description == "back"
        assert pics[1].picture_type == 4

    def test_mixed_single_and_multi_frames(self):
        fc = FrameCollection()
        fc.add(_text("TIT2", "Song"))
        fc.add(_text("TPE1", "Artist"))
        fc.add(_comm("eng", "", "English"))
        fc.add(_comm("spa", "", "Spanish"))

        built = build_id3(fc)
        parsed = parse_id3(built)["frames"]

        assert parsed["TIT2"].text == "Song"
        assert parsed["TPE1"].text == "Artist"
        assert len(parsed.get_all("COMM")) == 2
        assert len(parsed) == 4


class TestFrameCollectionAcceptedByTag:
    def test_tag_accepts_frame_collection(self):
        from trackula import Tag

        fc = FrameCollection([_text("TIT2", "Hello")])
        tag = Tag(fc)
        assert tag.title == "Hello"

    def test_tag_accepts_list(self):
        from trackula import Tag

        tag = Tag([_text("TIT2", "Hello")])
        assert tag.title == "Hello"

    def test_tag_accepts_dict_for_backward_compat(self):
        from trackula import Tag

        tag = Tag({"TIT2": _text("TIT2", "Hello")})
        assert tag.title == "Hello"
