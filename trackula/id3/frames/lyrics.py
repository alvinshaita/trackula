from typing import List

from ...frame import LyricsFrame, SyncedLyricsEntry, SyncedLyricsFrame
from ..encoding import (
    decode_by_encoding,
    encode_by_encoding,
    find_terminator,
    terminator_length,
)


def parse_lyrics(frame_id: str, data: bytes) -> LyricsFrame:
    # USLT structure (identical to COMM):
    #   encoding     1 byte
    #   language     3 bytes
    #   description  text in `encoding`, null-terminated
    #   text         text in `encoding`, rest of frame
    encoding = data[0]
    language = data[1:4].decode("latin1")

    desc_start = 4
    desc_end = find_terminator(data, desc_start, encoding)
    description = decode_by_encoding(data[desc_start:desc_end], encoding)

    text_start = desc_end + terminator_length(encoding)
    text = decode_by_encoding(data[text_start:], encoding)

    return LyricsFrame(
        frame_id=frame_id,
        language=language,
        description=description,
        text=text,
    )


def build_lyrics(frame: LyricsFrame) -> bytes:
    language = (frame.language[:3] + "\x00\x00\x00")[:3].encode("latin1")
    return (
        b"\x03"
        + language
        + encode_by_encoding(frame.description, 3)
        + b"\x00"
        + encode_by_encoding(frame.text, 3)
    )


def parse_synced_lyrics(frame_id: str, data: bytes) -> SyncedLyricsFrame:
    # SYLT structure:
    #   encoding         1 byte
    #   language         3 bytes
    #   timestamp format 1 byte (1=MPEG frames, 2=milliseconds)
    #   content type     1 byte
    #   descriptor       text in `encoding`, null-terminated
    #   entries          repeating: text in `encoding` + null terminator
    #                    + 4 bytes big-endian timestamp
    encoding = data[0]
    language = data[1:4].decode("latin1")
    timestamp_format = data[4]
    content_type = data[5]

    desc_start = 6
    desc_end = find_terminator(data, desc_start, encoding)
    description = decode_by_encoding(data[desc_start:desc_end], encoding)

    offset = desc_end + terminator_length(encoding)
    entries: List[SyncedLyricsEntry] = []

    while offset < len(data):
        text_end = find_terminator(data, offset, encoding)
        text = decode_by_encoding(data[offset:text_end], encoding)
        offset = text_end + terminator_length(encoding)
        if offset + 4 > len(data):
            break
        timestamp = int.from_bytes(data[offset:offset + 4], "big")
        offset += 4
        entries.append(SyncedLyricsEntry(text=text, timestamp=timestamp))

    return SyncedLyricsFrame(
        frame_id=frame_id,
        language=language,
        timestamp_format=timestamp_format,
        content_type=content_type,
        description=description,
        entries=entries,
    )


def build_synced_lyrics(frame: SyncedLyricsFrame) -> bytes:
    language = (frame.language[:3] + "\x00\x00\x00")[:3].encode("latin1")

    out = bytearray()
    out.append(3)  # encoding: UTF-8
    out.extend(language)
    out.append(frame.timestamp_format)
    out.append(frame.content_type)
    out.extend(encode_by_encoding(frame.description, 3))
    out.append(0)  # descriptor terminator

    for entry in frame.entries:
        out.extend(encode_by_encoding(entry.text, 3))
        out.append(0)  # entry text terminator
        out.extend(entry.timestamp.to_bytes(4, "big"))

    return bytes(out)
