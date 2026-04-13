FRIENDLY_NAMES = {
    "TIT2": "title",
    "TPE1": "artist",
    "TRCK": "track",
    "TALB": "album",
    "TPOS": "disc",
    "TCON": "genre",
    "TDAT": "date",
    "TYER": "year",
    "TOWN": "owner",
    "TPE2": "album_artist",
    "TSRC": "isrc",
    "TPUB": "publisher",
    "APIC": "picture",
}


class Tag:
    def __init__(self, frames=None):
        self.frames = frames or {}

    def get(self, key):
        return self.frames.get(key)

    def set(self, key, value):
        self.frames[key] = value


def _make_property(frame_id):
    def getter(self):
        return self.frames.get(frame_id)

    def setter(self, value):
        self.frames[frame_id] = value

    return property(getter, setter)


for _frame_id, _friendly in FRIENDLY_NAMES.items():
    _prop = _make_property(_frame_id)
    setattr(Tag, _frame_id, _prop)
    setattr(Tag, _friendly, _prop)
