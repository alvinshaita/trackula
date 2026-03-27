from .buffer import encode_synchsafe
from .text import encode_text

def build_id3(frames):
	frame_bytes = b""
	
	for frame_id, frame_data in frames.items():
		frame_bytes += build_text_frame(frame_id, frame_data)

	id3_header = build_header(len(frame_bytes))
	return id3_header + frame_bytes


def build_text_frame(frame_id, frame_data):
	if frame_id.startswith("T"):
		encoded_frame_data = encode_text(frame_data)
	else:
		encoded_frame_data = frame_data

	size = len(encoded_frame_data).to_bytes(4, "big")
	flags = b"\x00\x00"

	return frame_id.encode() + size + flags + encoded_frame_data


def build_header(size: int, version=3):
	header = b"ID3"\
		+ bytes([version, 0])\
		+ b"\x00"\
		+ encode_synchsafe(size)
	return header
