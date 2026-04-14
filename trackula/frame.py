import os
from dataclasses import dataclass
from typing import Union

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
    PictureFrame,
    CommentFrame,
    UrlFrame,
    UserUrlFrame,
    UnknownFrame,
]
