# trackula

A Python library for reading and writing ID3 tags on MP3 files. Supports ID3v1, ID3v1.1, ID3v2.3, and ID3v2.4.

## Installation

```bash
pip install -e .
```

## Usage

### Read and write tags

```python
from trackula import read, write

tag = read("song.mp3")
print(tag.title, tag.artist, tag.album)

tag.title = "New Title"
tag.artist = "New Artist"
write("song.mp3", tag)
```

### AudioFile for load-modify-save workflows

```python
from trackula import AudioFile

f = AudioFile("song.mp3")
f.tag.title = "Updated Title"
f.tag.artist = "Updated Artist"
f.save()

# Save a copy to a different path
f.save("copy.mp3")
```

### Extract album art

```python
from trackula import AudioFile

f = AudioFile("song.mp3")
pic = f.tag.picture
if pic:
    pic.save("cover.jpg")
    # or save to a directory (auto-names the file)
    pic.save("/output/")
```

### Attach album art

```python
from trackula import AudioFile, PictureFrame

f = AudioFile("song.mp3")
f.tag.frames["APIC"] = PictureFrame.from_file("cover.jpg")
f.save()
```

### Work with comments and lyrics

```python
from trackula import AudioFile, CommentFrame, LyricsFrame

f = AudioFile("song.mp3")

# Add a comment
f.tag.frames.add(CommentFrame("COMM", "eng", "", "Great track"))

# Add lyrics
f.tag.frames.add(LyricsFrame("USLT", "eng", "", "Row row row your boat..."))

f.save()
```

### Multiple frames with the same ID

Tags can carry multiple frames with the same ID (e.g. comments in different languages, front + back cover art). Use `add()` and `get_all()`:

```python
from trackula import AudioFile, CommentFrame

f = AudioFile("song.mp3")
f.tag.frames.add(CommentFrame("COMM", "eng", "Mood", "Chill"))
f.tag.frames.add(CommentFrame("COMM", "spa", "Estado", "Tranquilo"))

for comment in f.tag.frames.get_all("COMM"):
    print(comment.language, comment.text)
```

### ID3v1 fallback

Files with only an ID3v1 tag are read through the same interface. Fields are mapped to their ID3v2 equivalents (title to TIT2, artist to TPE1, etc.). Saving always writes ID3v2.

```python
from trackula import read

tag = read("old_song.mp3")  # works even if the file only has a v1 tag
print(tag.title, tag.artist)
```

## Supported frames

| Frame ID | Type | Fields |
|---|---|---|
| T*** (TIT2, TPE1, TALB, ...) | `TextFrame` | `text` |
| TXXX | `UserTextFrame` | `description`, `text` |
| APIC | `PictureFrame` | `mime`, `picture_type`, `description`, `data` |
| COMM | `CommentFrame` | `language`, `description`, `text` |
| USLT | `LyricsFrame` | `language`, `description`, `text` |
| SYLT | `SyncedLyricsFrame` | `language`, `timestamp_format`, `content_type`, `description`, `entries` |
| W*** (WOAR, WCOP, ...) | `UrlFrame` | `url` |
| WXXX | `UserUrlFrame` | `description`, `url` |
| POPM | `PopularimeterFrame` | `email`, `rating`, `counter` |
| UFID | `UniqueFileIdentifierFrame` | `owner`, `identifier` |
| PCNT | `PlayCountFrame` | `count` |
| GEOB | `GeneralObjectFrame` | `mime`, `filename`, `description`, `data` |
| (anything else) | `UnknownFrame` | `raw` (preserved as bytes) |

All frame dataclasses include a `frame_id` field. Unrecognized frames are preserved as `UnknownFrame` with their raw bytes intact, so round-tripping a file through trackula doesn't lose unknown frame data.

## Friendly property accessors on Tag

Common text frames have short aliases on the `Tag` object:

| Property | Frame ID |
|---|---|
| `tag.title` | TIT2 |
| `tag.artist` | TPE1 |
| `tag.album` | TALB |
| `tag.track` | TRCK |
| `tag.year` | TYER |
| `tag.genre` | TCON |
| `tag.album_artist` | TPE2 |
| `tag.disc` | TPOS |
| `tag.date` | TDAT |
| `tag.owner` | TOWN |
| `tag.isrc` | TSRC |
| `tag.publisher` | TPUB |
| `tag.picture` | APIC |

These return plain strings for text frames and Frame objects for non-text frames.

## File structure

```
trackula/
├── pyproject.toml
└── trackula/
    ├── __init__.py             # public API re-exports
    ├── api.py                  # read() / write()
    ├── audiofile.py            # AudioFile class
    ├── tag.py                  # Tag model with friendly accessors
    ├── frame.py                # Frame dataclasses + FrameCollection
    ├── errors.py               # ID3Error, InvalidHeaderError
    ├── id3/                    # pure ID3v2 spec logic (no file I/O)
    │   ├── synchsafe.py        # synchsafe integer codec
    │   ├── encoding.py         # text encoding / decoding helpers
    │   ├── header.py           # parse_header / build_header
    │   ├── parser.py           # parse_id3 (with extended header support)
    │   ├── builder.py          # build_id3
    │   └── frames/             # per-frame-type parsers and builders
    │       ├── text.py         # T*** text frames
    │       ├── user_text.py    # TXXX
    │       ├── picture.py      # APIC
    │       ├── comment.py      # COMM
    │       ├── lyrics.py       # USLT + SYLT
    │       ├── url.py          # W*** + WXXX
    │       ├── popm.py         # POPM
    │       ├── ufid.py         # UFID
    │       ├── pcnt.py         # PCNT
    │       ├── geob.py         # GEOB
    │       └── unknown.py      # fallback for unrecognized frames
    └── containers/             # per-format file framing
        └── mp3.py              # MP3 split/write + ID3v1 parsing
```
