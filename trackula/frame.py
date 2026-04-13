from dataclasses import dataclass, field
from typing import Union


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
