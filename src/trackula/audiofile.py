from .api import read, write
from .tag import Tag


class AudioFile:
    def __init__(self, path: str):
        self.path = path
        self.tag: Tag = read(path)

    def save(self, output: str = None) -> None:
        write(output or self.path, self.tag)

    def __repr__(self) -> str:
        return f"AudioFile({self.path!r})"
