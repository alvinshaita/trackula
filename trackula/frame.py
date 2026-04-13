from dataclasses import dataclass
from typing import Union


@dataclass
class TextFrame:
    frame_id: str
    text: str


@dataclass
class UnknownFrame:
    frame_id: str
    raw: bytes


Frame = Union[TextFrame, UnknownFrame]
