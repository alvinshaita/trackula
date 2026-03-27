from typing import Tuple
from ..id3.buffer import decode_synchsafe

def split_audio_data(path: str) -> Tuple[bytes, bytes]:
	with open(path, "rb") as f:
		header = f.read(10)
		if header[:3] == b"ID3":
			# id3v2

			encoded_tag_size = header[6:10]
			tag_size = decode_synchsafe(encoded_tag_size)
			f.seek(0)
			tag_bytes = f.read(10 + tag_size)
			audio_bytes = f.read()
		else:
			print("NOT header id3")
			f.seek(0)
			tag_bytes = b""
			audio_bytes = f.read()

	return tag_bytes, audio_bytes
