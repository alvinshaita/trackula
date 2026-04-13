from dataclasses import dataclass


@dataclass
class TextFrame:
    frame_id: str
    text: str


@dataclass
class UnknownFrame:
    frame_id: str
    raw: bytes
