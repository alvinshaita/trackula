import os
from dataclasses import dataclass, field, fields
from typing import Iterable, Iterator, List, Optional, Tuple, Union

FIELD_REPR_LIMIT = 50

_MIME_TO_EXTENSION = {
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/png": "png",
    "image/gif": "gif",
    "image/webp": "webp",
    "image/bmp": "bmp",
    "image/tiff": "tiff",
}

_EXTENSION_TO_MIME = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "gif": "image/gif",
    "webp": "image/webp",
    "bmp": "image/bmp",
    "tiff": "image/tiff",
    "tif": "image/tiff",
}


@dataclass
class TextFrame:
    frame_id: str
    text: str


@dataclass
class PictureFrame:
    frame_id: str
    mime: str
    picture_type: int
    description: str
    data: bytes

    @property
    def extension(self) -> str:
        """File extension for this picture's mime type, or 'bin' if unknown."""
        return _MIME_TO_EXTENSION.get(self.mime, "bin")

    def save(self, path: str, add_extension: bool = False) -> str:
        """Write the picture's image bytes to `path` and return the written path.

        If `path` is an existing directory, a file is created inside it named
        after the frame's description (or "cover" if description is empty),
        with an extension matching the picture's mime type. The
        `add_extension` keyword is ignored in this case since a fresh name
        needs an extension anyway.

        If `path` is a file path and `add_extension` is True, the mime-type
        extension is appended unconditionally — so
        `save("cover.jpg", add_extension=True)` on a JPEG produces
        `cover.jpg.jpg`. When `add_extension` is False (the default), the
        path is used as given.
        """
        if os.path.isdir(path):
            name = self.description or "cover"
            path = os.path.join(path, f"{name}.{self.extension}")
        elif add_extension:
            path = f"{path}.{self.extension}"

        with open(path, "wb") as f:
            f.write(self.data)

        return path

    @classmethod
    def from_file(
        cls,
        path: str,
        picture_type: int = 3,
        description: str = "",
    ) -> "PictureFrame":
        """Load an image file into a PictureFrame.

        The MIME type is inferred from the file extension. `picture_type`
        defaults to 3 (front cover) — see the ID3v2 APIC spec for the full
        list of valid values.
        """
        ext = os.path.splitext(path)[1].lstrip(".").lower()
        mime = _EXTENSION_TO_MIME.get(ext, "application/octet-stream")
        with open(path, "rb") as f:
            data = f.read()
        return cls(
            frame_id="APIC",
            mime=mime,
            picture_type=picture_type,
            description=description,
            data=data,
        )


@dataclass
class CommentFrame:
    frame_id: str
    language: str
    description: str
    text: str


@dataclass
class LyricsFrame:
    """USLT — unsynchronised lyric / text transcription. Same shape as COMM."""
    frame_id: str
    language: str
    description: str
    text: str


@dataclass
class SyncedLyricsEntry:
    text: str
    timestamp: int


@dataclass
class SyncedLyricsFrame:
    """SYLT — synchronised lyrics with timestamped text entries."""
    frame_id: str
    language: str
    timestamp_format: int  # 1 = MPEG frames, 2 = milliseconds
    content_type: int  # 0=other, 1=lyrics, 2=transcription, 3=movement, ...
    description: str
    entries: List[SyncedLyricsEntry] = field(default_factory=list)


@dataclass
class UserTextFrame:
    """TXXX — user-defined text information. Description + value."""
    frame_id: str
    description: str
    text: str


@dataclass
class PopularimeterFrame:
    """POPM — popularimeter. Per-user rating and play counter."""
    frame_id: str
    email: str
    rating: int  # 0 = unknown, 1..255 = rating value
    counter: int


@dataclass
class UniqueFileIdentifierFrame:
    """UFID — unique file identifier. Owner URL + binary identifier."""
    frame_id: str
    owner: str
    identifier: bytes


@dataclass
class PlayCountFrame:
    """PCNT — plain integer play counter."""
    frame_id: str
    count: int


@dataclass
class GeneralObjectFrame:
    """GEOB — general encapsulated object. Arbitrary binary with metadata."""
    frame_id: str
    mime: str
    filename: str
    description: str
    data: bytes


@dataclass
class UrlFrame:
    frame_id: str
    url: str


@dataclass
class UserUrlFrame:
    frame_id: str
    description: str
    url: str


@dataclass
class UnknownFrame:
    frame_id: str
    raw: bytes


Frame = Union[
    TextFrame,
    UserTextFrame,
    PictureFrame,
    CommentFrame,
    LyricsFrame,
    SyncedLyricsFrame,
    PopularimeterFrame,
    UniqueFileIdentifierFrame,
    PlayCountFrame,
    GeneralObjectFrame,
    UrlFrame,
    UserUrlFrame,
    UnknownFrame,
]


def _truncate_field_repr(value: object) -> str:
    s = repr(value)
    if len(s) > FIELD_REPR_LIMIT:
        return s[:FIELD_REPR_LIMIT] + "..."
    return s


def _frame_repr(self) -> str:
    parts = [
        f"{f.name}={_truncate_field_repr(getattr(self, f.name))}"
        for f in fields(self)
    ]
    return f"{type(self).__name__}({', '.join(parts)})"


for _cls in (
    TextFrame,
    UserTextFrame,
    PictureFrame,
    CommentFrame,
    LyricsFrame,
    SyncedLyricsEntry,
    SyncedLyricsFrame,
    PopularimeterFrame,
    UniqueFileIdentifierFrame,
    PlayCountFrame,
    GeneralObjectFrame,
    UrlFrame,
    UserUrlFrame,
    UnknownFrame,
):
    _cls.__repr__ = _frame_repr
del _cls


class FrameCollection:
    """Ordered collection of frames that allows multiple frames per frame id.

    Frames like COMM, APIC, USLT, WXXX, and TXXX can legitimately appear more
    than once in a single tag, disambiguated by description or language. A
    plain Dict[str, Frame] can only store one per id, so FrameCollection
    backs itself with a list and exposes both dict-style access (first match
    wins) and list-style helpers for the multi-frame cases.

    The single-frame path stays ergonomic:
        tag.frames["TIT2"] = TextFrame("TIT2", "Hello")
        tag.frames["TIT2"].text

    For multi-frame cases use add() and get_all():
        tag.frames.add(CommentFrame("COMM", "eng", "", "note in English"))
        tag.frames.add(CommentFrame("COMM", "spa", "", "nota en español"))
        for c in tag.frames.get_all("COMM"):
            ...

    Assigning via __setitem__ replaces *all* existing frames with that id.
    Use add() to preserve existing frames with the same id.
    """

    def __init__(self, frames: Optional[Iterable[Frame]] = None) -> None:
        self._frames: List[Frame] = list(frames) if frames else []

    # --- container protocol ---------------------------------------------------

    def __len__(self) -> int:
        return len(self._frames)

    def __iter__(self) -> Iterator[Frame]:
        return iter(self._frames)

    def __contains__(self, frame_id: object) -> bool:
        return any(f.frame_id == frame_id for f in self._frames)

    def __getitem__(self, frame_id: str) -> Frame:
        for f in self._frames:
            if f.frame_id == frame_id:
                return f
        raise KeyError(frame_id)

    def __setitem__(self, frame_id: str, frame: Frame) -> None:
        """Replace all existing frames with this id with the given frame."""
        self._frames = [f for f in self._frames if f.frame_id != frame_id]
        self._frames.append(frame)

    def __delitem__(self, frame_id: str) -> None:
        kept = [f for f in self._frames if f.frame_id != frame_id]
        if len(kept) == len(self._frames):
            raise KeyError(frame_id)
        self._frames = kept

    def __eq__(self, other: object) -> bool:
        if isinstance(other, FrameCollection):
            return self._frames == other._frames
        if isinstance(other, list):
            return self._frames == other
        return NotImplemented

    def __repr__(self) -> str:
        return f"FrameCollection({self._frames!r})"

    # --- lookup ---------------------------------------------------------------

    def get(
        self, frame_id: str, default: Optional[Frame] = None
    ) -> Optional[Frame]:
        """Return the first frame with this id, or `default` if none."""
        try:
            return self[frame_id]
        except KeyError:
            return default

    def get_all(self, frame_id: str) -> List[Frame]:
        """Return all frames with this id in insertion order."""
        return [f for f in self._frames if f.frame_id == frame_id]

    # --- mutation -------------------------------------------------------------

    def add(self, frame: Frame) -> None:
        """Append a frame, preserving any existing frames with the same id.

        Use this to add multiple frames with the same id (e.g. multiple COMM
        frames in different languages). Use __setitem__ to replace instead.
        """
        self._frames.append(frame)

    def remove_all(self, frame_id: str) -> int:
        """Remove all frames with this id. Returns the count removed."""
        before = len(self._frames)
        self._frames = [f for f in self._frames if f.frame_id != frame_id]
        return before - len(self._frames)

    def clear(self) -> None:
        self._frames = []

    # --- dict-like views ------------------------------------------------------

    def frame_ids(self) -> List[str]:
        """Return unique frame ids in first-occurrence order."""
        seen: List[str] = []
        for f in self._frames:
            if f.frame_id not in seen:
                seen.append(f.frame_id)
        return seen

    def keys(self) -> List[str]:
        """Alias for frame_ids() — unique ids in first-occurrence order."""
        return self.frame_ids()

    def values(self) -> List[Frame]:
        """Return all frames as a list, including duplicates."""
        return list(self._frames)

    def items(self) -> List[Tuple[str, Frame]]:
        """Return (frame_id, frame) tuples, one per frame including duplicates."""
        return [(f.frame_id, f) for f in self._frames]
