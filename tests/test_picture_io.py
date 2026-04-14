import pytest

from trackula.frame import PictureFrame

PNG_MAGIC = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16
JPEG_MAGIC = b"\xff\xd8\xff\xe0" + b"\x00" * 16


def _png_frame(description=""):
    return PictureFrame(
        frame_id="APIC",
        mime="image/png",
        picture_type=3,
        description=description,
        data=PNG_MAGIC,
    )


def _jpeg_frame(description=""):
    return PictureFrame(
        frame_id="APIC",
        mime="image/jpeg",
        picture_type=3,
        description=description,
        data=JPEG_MAGIC,
    )


class TestExtension:
    def test_png(self):
        assert _png_frame().extension == "png"

    def test_jpeg(self):
        assert _jpeg_frame().extension == "jpg"

    def test_gif(self):
        frame = PictureFrame("APIC", "image/gif", 3, "", b"")
        assert frame.extension == "gif"

    def test_webp(self):
        frame = PictureFrame("APIC", "image/webp", 3, "", b"")
        assert frame.extension == "webp"

    def test_unknown_mime_falls_back_to_bin(self):
        frame = PictureFrame("APIC", "application/weird", 3, "", b"")
        assert frame.extension == "bin"


class TestSaveToFilePath:
    def test_writes_bytes_to_path(self, tmp_path):
        target = tmp_path / "cover.jpg"
        returned = _jpeg_frame().save(str(target))
        assert returned == str(target)
        assert target.read_bytes() == JPEG_MAGIC

    def test_add_extension_false_by_default(self, tmp_path):
        target = tmp_path / "cover"
        returned = _jpeg_frame().save(str(target))
        assert returned == str(target)
        assert target.exists()
        assert not (tmp_path / "cover.jpg").exists()

    def test_add_extension_true_appends_extension(self, tmp_path):
        target = tmp_path / "cover"
        returned = _jpeg_frame().save(str(target), add_extension=True)
        assert returned == str(target) + ".jpg"
        assert (tmp_path / "cover.jpg").read_bytes() == JPEG_MAGIC

    def test_add_extension_true_appends_unconditionally(self, tmp_path):
        # Per spec: add_extension=True appends regardless of what the name
        # already looks like. "cover.jpg" on a jpeg becomes "cover.jpg.jpg".
        target = tmp_path / "cover.jpg"
        returned = _jpeg_frame().save(str(target), add_extension=True)
        assert returned == str(target) + ".jpg"
        assert (tmp_path / "cover.jpg.jpg").read_bytes() == JPEG_MAGIC

    def test_overwrites_existing_file(self, tmp_path):
        target = tmp_path / "cover.jpg"
        target.write_bytes(b"old content")
        _jpeg_frame().save(str(target))
        assert target.read_bytes() == JPEG_MAGIC


class TestSaveToDirectory:
    def test_uses_cover_when_description_empty(self, tmp_path):
        returned = _png_frame(description="").save(str(tmp_path))
        expected = tmp_path / "cover.png"
        assert returned == str(expected)
        assert expected.read_bytes() == PNG_MAGIC

    def test_uses_description_when_non_empty(self, tmp_path):
        returned = _jpeg_frame(description="album_art").save(str(tmp_path))
        expected = tmp_path / "album_art.jpg"
        assert returned == str(expected)
        assert expected.read_bytes() == JPEG_MAGIC

    def test_directory_path_ignores_add_extension_flag(self, tmp_path):
        # The dir case always adds the extension; the flag is moot.
        a = _png_frame().save(str(tmp_path), add_extension=False)
        (tmp_path / "cover.png").unlink()
        b = _png_frame().save(str(tmp_path), add_extension=True)
        assert a == b

    def test_unknown_mime_gets_bin_extension_in_dir(self, tmp_path):
        frame = PictureFrame("APIC", "application/weird", 3, "", PNG_MAGIC)
        returned = frame.save(str(tmp_path))
        assert returned == str(tmp_path / "cover.bin")


class TestFromFile:
    def test_reads_png(self, tmp_path):
        src = tmp_path / "image.png"
        src.write_bytes(PNG_MAGIC)

        frame = PictureFrame.from_file(str(src))
        assert isinstance(frame, PictureFrame)
        assert frame.frame_id == "APIC"
        assert frame.mime == "image/png"
        assert frame.picture_type == 3
        assert frame.description == ""
        assert frame.data == PNG_MAGIC

    def test_reads_jpg(self, tmp_path):
        src = tmp_path / "image.jpg"
        src.write_bytes(JPEG_MAGIC)

        frame = PictureFrame.from_file(str(src))
        assert frame.mime == "image/jpeg"
        assert frame.data == JPEG_MAGIC

    def test_jpeg_extension_also_works(self, tmp_path):
        src = tmp_path / "image.jpeg"
        src.write_bytes(JPEG_MAGIC)
        assert PictureFrame.from_file(str(src)).mime == "image/jpeg"

    def test_uppercase_extension(self, tmp_path):
        src = tmp_path / "image.PNG"
        src.write_bytes(PNG_MAGIC)
        assert PictureFrame.from_file(str(src)).mime == "image/png"

    def test_unknown_extension_falls_back(self, tmp_path):
        src = tmp_path / "image.xyz"
        src.write_bytes(b"whatever")
        assert PictureFrame.from_file(str(src)).mime == "application/octet-stream"

    def test_picture_type_override(self, tmp_path):
        src = tmp_path / "image.png"
        src.write_bytes(PNG_MAGIC)
        frame = PictureFrame.from_file(str(src), picture_type=0x11)
        assert frame.picture_type == 0x11

    def test_description_override(self, tmp_path):
        src = tmp_path / "image.png"
        src.write_bytes(PNG_MAGIC)
        frame = PictureFrame.from_file(str(src), description="Back cover")
        assert frame.description == "Back cover"

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            PictureFrame.from_file(str(tmp_path / "nope.png"))


def test_round_trip_from_file_and_save(tmp_path):
    src = tmp_path / "original.png"
    src.write_bytes(PNG_MAGIC)

    frame = PictureFrame.from_file(str(src))
    out = tmp_path / "copy.png"
    frame.save(str(out))

    assert out.read_bytes() == PNG_MAGIC
