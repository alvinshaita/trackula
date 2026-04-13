from trackula.frame import PictureFrame
from trackula.id3.builder import build_id3
from trackula.id3.frames import build_frame, parse_frames
from trackula.id3.parser import parse_id3

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def _make_picture(mime="image/png", ptype=3, desc="cover", data=PNG_MAGIC):
    return PictureFrame(
        frame_id="APIC",
        mime=mime,
        picture_type=ptype,
        description=desc,
        data=data,
    )


class TestBuildPicture:
    def test_starts_with_apic_id(self):
        result = build_frame(_make_picture())
        assert result[:4] == b"APIC"

    def test_mime_is_latin1(self):
        # Frame body starts after 10-byte header; first is encoding byte, then mime + \0
        result = build_frame(_make_picture(mime="image/jpeg"))
        body = result[10:]
        assert body[0:1] == b"\x03"  # utf-8 encoding byte
        assert body[1:11] == b"image/jpeg"
        assert body[11:12] == b"\x00"

    def test_preserves_binary_data(self):
        blob = bytes(range(256))
        result = build_frame(_make_picture(data=blob))
        assert result.endswith(blob)


class TestParsePicture:
    def test_round_trip_defaults(self):
        original = _make_picture()
        built = build_id3({"APIC": original})
        parsed = parse_id3(built)["frames"]["APIC"]

        assert isinstance(parsed, PictureFrame)
        assert parsed.frame_id == "APIC"
        assert parsed.mime == "image/png"
        assert parsed.picture_type == 3
        assert parsed.description == "cover"
        assert parsed.data == PNG_MAGIC

    def test_round_trip_empty_description(self):
        original = _make_picture(desc="")
        built = build_id3({"APIC": original})
        parsed = parse_id3(built)["frames"]["APIC"]
        assert parsed.description == ""
        assert parsed.data == PNG_MAGIC

    def test_round_trip_unicode_description(self):
        original = _make_picture(desc="Álbum cover 🎵")
        built = build_id3({"APIC": original})
        parsed = parse_id3(built)["frames"]["APIC"]
        assert parsed.description == "Álbum cover 🎵"

    def test_round_trip_preserves_binary_data(self):
        blob = bytes(range(256))
        original = _make_picture(data=blob)
        built = build_id3({"APIC": original})
        parsed = parse_id3(built)["frames"]["APIC"]
        assert parsed.data == blob

    def test_round_trip_picture_type_value(self):
        original = _make_picture(ptype=0x11)  # band/orchestra
        built = build_id3({"APIC": original})
        parsed = parse_id3(built)["frames"]["APIC"]
        assert parsed.picture_type == 0x11

    def test_parses_via_frames_dispatch(self):
        # regression: parser must route APIC to parse_picture, not parse_unknown
        built = build_id3({"APIC": _make_picture()})
        parsed = parse_frames(built[10:], version=4)
        assert isinstance(parsed["APIC"], PictureFrame)
