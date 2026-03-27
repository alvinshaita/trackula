from .io.file import split_audio_data, write_audio_file
from .id3.builder import build_id3

def write(path, tag):
	_, audio_bytes = split_audio_data(path)
	tag_bytes = build_id3(tag.frames)
	write_audio_file(path, tag_bytes, audio_bytes)
