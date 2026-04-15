from typing import NamedTuple

from ..frame import CommentFrame, FrameCollection, TextFrame
from ..id3.synchsafe import decode_int

ID3V2_MAGIC = b"ID3"
ID3V2_HEADER_SIZE = 10

ID3V1_MAGIC = b"TAG"
ID3V1_SIZE = 128

# ID3v1 genre list (first 80 entries — the only values defined by the original
# spec). Winamp later extended this to ~148 but we stick to the portable set.
# Index maps directly to the byte at position 127 of the v1 tag.
_V1_GENRES = (
    "Blues", "Classic Rock", "Country", "Dance", "Disco", "Funk", "Grunge",
    "Hip-Hop", "Jazz", "Metal", "New Age", "Oldies", "Other", "Pop", "R&B",
    "Rap", "Reggae", "Rock", "Techno", "Industrial", "Alternative", "Ska",
    "Death Metal", "Pranks", "Soundtrack", "Euro-Techno", "Ambient",
    "Trip-Hop", "Vocal", "Jazz+Funk", "Fusion", "Trance", "Classical",
    "Instrumental", "Acid", "House", "Game", "Sound Clip", "Gospel", "Noise",
    "AlternRock", "Bass", "Soul", "Punk", "Space", "Meditative",
    "Instrumental Pop", "Instrumental Rock", "Ethnic", "Gothic", "Darkwave",
    "Techno-Industrial", "Electronic", "Pop-Folk", "Eurodance", "Dream",
    "Southern Rock", "Comedy", "Cult", "Gangsta", "Top 40", "Christian Rap",
    "Pop/Funk", "Jungle", "Native American", "Cabaret", "New Wave",
    "Psychadelic", "Rave", "Showtunes", "Trailer", "Lo-Fi", "Tribal",
    "Acid Punk", "Acid Jazz", "Polka", "Retro", "Musical", "Rock & Roll",
    "Hard Rock",
)


class Mp3Split(NamedTuple):
    """Result of splitting an MP3 file into its three byte regions."""
    v2_tag: bytes   # ID3v2 tag bytes at the start of the file (b"" if absent)
    audio: bytes    # MPEG audio payload with v1 and v2 stripped
    v1_tag: bytes   # 128-byte ID3v1 footer at the end (b"" if absent)


def split_mp3(path: str) -> Mp3Split:
    """Split an MP3 file into its ID3v2 tag, audio body, and ID3v1 footer.

    Both tag regions are optional — if either is missing the corresponding
    field in the returned Mp3Split is an empty bytes object. The `audio`
    field always holds the pure MPEG payload with both tags removed, so
    callers that want to rewrite only the tag can safely write
    `new_v2_tag + split.audio` without accidentally duplicating a v1 footer.
    """
    with open(path, "rb") as f:
        f.seek(0, 2)
        filesize = f.tell()

        v2_tag = b""
        audio_start = 0
        if filesize >= ID3V2_HEADER_SIZE:
            f.seek(0)
            header = f.read(ID3V2_HEADER_SIZE)
            if header[:3] == ID3V2_MAGIC:
                size_bytes = header[6:10]
                tag_size = decode_int(size_bytes, synchsafe=True)
                v2_end = ID3V2_HEADER_SIZE + tag_size
                f.seek(0)
                v2_tag = f.read(v2_end)
                audio_start = v2_end

        v1_tag = b""
        audio_end = filesize
        if filesize - audio_start >= ID3V1_SIZE:
            f.seek(filesize - ID3V1_SIZE)
            candidate = f.read(ID3V1_SIZE)
            if candidate[:3] == ID3V1_MAGIC:
                v1_tag = candidate
                audio_end = filesize - ID3V1_SIZE

        audio_size = max(0, audio_end - audio_start)
        if audio_size > 0:
            f.seek(audio_start)
            audio = f.read(audio_size)
        else:
            audio = b""

    return Mp3Split(v2_tag=v2_tag, audio=audio, v1_tag=v1_tag)


def write_mp3(path: str, tag_bytes: bytes, audio_bytes: bytes) -> None:
    with open(path, "wb") as f:
        f.write(tag_bytes + audio_bytes)


def parse_v1_tag(v1_bytes: bytes) -> FrameCollection:
    """Parse a 128-byte ID3v1 / ID3v1.1 tag into a FrameCollection.

    Maps the fixed v1 fields to equivalent ID3v2 frames so callers can use
    the same Tag interface regardless of which version the source file
    carried:

    - title    -> TIT2
    - artist   -> TPE1
    - album    -> TALB
    - year     -> TYER
    - comment  -> COMM (language "eng", empty description)
    - track    -> TRCK  (only present when the tag is v1.1)
    - genre    -> TCON  (resolved from the genre index to a human name)

    Empty fields are skipped so the resulting collection reflects only the
    data that was actually set. Returns an empty FrameCollection if the
    input doesn't start with the "TAG" magic or isn't exactly 128 bytes.
    """
    if len(v1_bytes) != ID3V1_SIZE or v1_bytes[:3] != ID3V1_MAGIC:
        return FrameCollection()

    fields = _parse_v1_fields(v1_bytes)
    return _v1_fields_to_frames(fields)


def _parse_v1_fields(v1_bytes: bytes) -> dict:
    """Parse a 128-byte v1 tag into a dict of raw field values.

    Fields that are empty after null/whitespace stripping remain as empty
    strings so the caller can distinguish "present but empty" from "absent";
    both cases end up skipped at the frame construction step.
    """
    title = _decode_v1_text(v1_bytes[3:33])
    artist = _decode_v1_text(v1_bytes[33:63])
    album = _decode_v1_text(v1_bytes[63:93])
    year = _decode_v1_text(v1_bytes[93:97])

    # v1.1 marker: byte 125 is 0 AND byte 126 is non-zero -> byte 126 is the
    # track number and the comment is only 28 bytes. Original v1 uses all 30
    # bytes for the comment.
    if v1_bytes[125] == 0 and v1_bytes[126] != 0:
        comment = _decode_v1_text(v1_bytes[97:125])
        track = v1_bytes[126]
    else:
        comment = _decode_v1_text(v1_bytes[97:127])
        track = None

    genre_index = v1_bytes[127]
    genre = _V1_GENRES[genre_index] if genre_index < len(_V1_GENRES) else None

    return {
        "title": title,
        "artist": artist,
        "album": album,
        "year": year,
        "comment": comment,
        "track": track,
        "genre": genre,
    }


def _v1_fields_to_frames(fields: dict) -> FrameCollection:
    fc = FrameCollection()

    if fields["title"]:
        fc.add(TextFrame(frame_id="TIT2", text=fields["title"]))
    if fields["artist"]:
        fc.add(TextFrame(frame_id="TPE1", text=fields["artist"]))
    if fields["album"]:
        fc.add(TextFrame(frame_id="TALB", text=fields["album"]))
    if fields["year"]:
        fc.add(TextFrame(frame_id="TYER", text=fields["year"]))
    if fields["comment"]:
        fc.add(CommentFrame(
            frame_id="COMM",
            language="eng",
            description="",
            text=fields["comment"],
        ))
    if fields["track"] is not None:
        fc.add(TextFrame(frame_id="TRCK", text=str(fields["track"])))
    if fields["genre"] is not None:
        fc.add(TextFrame(frame_id="TCON", text=fields["genre"]))

    return fc


def _decode_v1_text(raw: bytes) -> str:
    """Decode a latin-1 v1 field, stripping null and whitespace padding."""
    return raw.rstrip(b"\x00 ").decode("latin1", errors="replace")
