# trackula

A small Python library for reading and writing ID3 tags on MP3 files.

## Usage

```python
from trackula import read, write

tag = read("song.mp3")
tag.title = "New Title"
tag.artist = "New Artist"
write("song.mp3", tag)
```

## File structure

```
trackula/
├── LICENSE
├── README.md
├── pyproject.toml
└── trackula/
    ├── __init__.py          # public API re-exports
    ├── api.py               # read() / write() entry points
    ├── audiofile.py         # AudioFile class (load / save lifecycle)
    ├── tag.py               # Tag model, friendly frame aliases
    ├── frame.py             # Frame dataclasses (TextFrame, UnknownFrame, ...)
    ├── errors.py            # ID3Error, InvalidHeaderError
    ├── id3/                 # pure ID3 spec logic (no file I/O)
    │   ├── __init__.py
    │   ├── synchsafe.py     # synchsafe integer codec
    │   ├── encoding.py      # text encoding codec
    │   ├── header.py        # parse_header / build_header
    │   ├── frames.py        # parse_frames / build_frames
    │   ├── parser.py        # parse_id3
    │   └── builder.py       # build_id3
    └── containers/          # per-format file framing
        ├── __init__.py
        └── mp3.py           # split_mp3 / write_mp3
```
