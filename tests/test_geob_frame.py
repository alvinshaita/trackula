from trackula.frame import GeneralObjectFrame
from trackula.id3.builder import build_id3
from trackula.id3.frames import parse_frames
from trackula.id3.parser import parse_id3


class TestGEOB:
    def test_round_trip(self):
        original = GeneralObjectFrame(
            frame_id="GEOB",
            mime="application/pdf",
            filename="liner_notes.pdf",
            description="Album liner notes",
            data=b"%PDF-1.4\n...fake pdf content...",
        )
        built = build_id3({"GEOB": original})
        parsed = parse_id3(built)["frames"]["GEOB"]

        assert isinstance(parsed, GeneralObjectFrame)
        assert parsed.mime == "application/pdf"
        assert parsed.filename == "liner_notes.pdf"
        assert parsed.description == "Album liner notes"
        assert parsed.data == b"%PDF-1.4\n...fake pdf content..."

    def test_empty_strings(self):
        original = GeneralObjectFrame("GEOB", "", "", "", b"payload")
        built = build_id3({"GEOB": original})
        parsed = parse_id3(built)["frames"]["GEOB"]
        assert parsed.mime == ""
        assert parsed.filename == ""
        assert parsed.description == ""
        assert parsed.data == b"payload"

    def test_binary_data(self):
        blob = bytes(range(256))
        original = GeneralObjectFrame(
            "GEOB", "application/octet-stream", "data.bin", "", blob
        )
        built = build_id3({"GEOB": original})
        parsed = parse_id3(built)["frames"]["GEOB"]
        assert parsed.data == blob

    def test_unicode_metadata(self):
        original = GeneralObjectFrame(
            "GEOB", "text/plain", "notas.txt", "Descripción ñ", b"content"
        )
        built = build_id3({"GEOB": original})
        parsed = parse_id3(built)["frames"]["GEOB"]
        assert parsed.filename == "notas.txt"
        assert parsed.description == "Descripción ñ"

    def test_routed_to_geob_parser(self):
        built = build_id3({
            "GEOB": GeneralObjectFrame("GEOB", "text/plain", "a.txt", "", b"x")
        })
        parsed = parse_frames(built[10:], version=4)
        assert isinstance(parsed["GEOB"], GeneralObjectFrame)

    def test_empty_data(self):
        original = GeneralObjectFrame(
            "GEOB", "text/plain", "empty.txt", "", b""
        )
        built = build_id3({"GEOB": original})
        parsed = parse_id3(built)["frames"]["GEOB"]
        assert parsed.data == b""
