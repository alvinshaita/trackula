from .buffer import encode_int
from .text import encode_text

def build_id3(frames, version=4):
	frame_bytes = build_frames(frames, version=version)
	frames_size = len(frame_bytes)
	id3_header = build_header(frames_size, version=version)
	
	id3_content = id3_header + frame_bytes
	return id3_content


def build_frames(frames, version=4):
	frame_bytes = b""
	for frame_id, frame_data in frames.items():
		frame_bytes += build_text_frame(frame_id, frame_data, version=version)

	return frame_bytes


def build_text_frame(frame_id, frame_data, version=4):
	if frame_id.startswith("T"):
		encoded_frame_data = encode_text(frame_data, 1)
	else:
		encoded_frame_data = frame_data

	size_bytes = len(encoded_frame_data)
	if version == 4:
		size = encode_int(size_bytes, synchsafe=True)
	else:
		size = encode_int(size_bytes, synchsafe=False)

	flags = b"\x00\x00"

	text_frame = frame_id.encode() + size + flags + encoded_frame_data
	return text_frame


def build_header(size: int, version=4):
	# ID3 tag size is ALWAYS synchsafe (v2.3 + v2.4)
	header = b"ID3"\
		+ bytes([version, 0])\
		+ b"\x00"\
		+ encode_int(size, synchsafe=True)

	return header
