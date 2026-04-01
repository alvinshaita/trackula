from typing import Tuple
from ..id3.buffer import decode_int

def split_audio_data(path: str) -> Tuple[bytes, bytes]:
	with open(path, "rb") as f:
		header = f.read(10)
		if header[:3] == b"ID3":
			# In ID3v2.3 and v2.4, there may be an extended header.
			# I'm assuming frames start after exactly 10 bytes meant for headers
			# TODO: Include check for extended headers

			flags = header[5]
			# has_extended_header = bool(flags & 0x40)

			size_bytes = header[6:10]
			# ID3 tag size is ALWAYS synchsafe (v2.3 + v2.4)
			tag_size = decode_int(size_bytes, synchsafe=True)
			f.seek(0)
			tag_bytes = f.read(10 + tag_size)
			audio_bytes = f.read()
		else:
			print("NOT header id3")
			f.seek(0)
			tag_bytes = b""
			audio_bytes = f.read()

	return tag_bytes, audio_bytes


def write_audio_file(path: str, tag_bytes: bytes, audio_bytes: bytes):
	with open(path, "wb") as f:
		f.write(tag_bytes + audio_bytes)
