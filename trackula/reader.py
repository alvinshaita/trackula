from .io.file import split_audio_data
from .id3.parser import parse_id3
from .models.tag import Tag

def read(path):
	tag_bytes, audio_bytes = split_audio_data(path)
	parsed = parse_id3(tag_bytes)
	return Tag(parsed["frames"])
