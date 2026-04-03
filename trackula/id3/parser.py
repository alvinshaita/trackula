from struct import unpack

from .buffer import decode_int
from .text import decode_text

def parse_id3(data: bytes):
	header = parse_header(data[:10])
	
	# TODO: extended headers awareness
	frames_body = data[10:10+header["size"]]
	frames = parse_frames(frames_body, header["version"])

	return {
		"header": header,
		"frames": frames,
	}


def parse_header(data: bytes):
	# main header is always 10 bytes long
	# in ID3v2, header is located at the beginning of the file
	# identifier: 3 bytes - always "ID3"
	# version: 	  2 bytes - major version and revision eg. 03 00 for v2.3.0
	# flags:      1 byte  - bitwise indicator
	# size:       4 bytes - total size of the tag, excluding 10 byte header

	if len(data) < 10:
		raise Exception("ID3 header data too short")

	identifier, version, revision, flags, size_bytes = unpack('>3sBBB4s', data)
	if identifier != b"ID3":
		raise Exception("Missing ID3 identifier")

	size = decode_int(size_bytes, synchsafe=True)

	return {
		"version": version,
		"revision": revision,
		"flags": flags,
		"size": size,
	}


def parse_frames(data: bytes, version: int):
	# each frame consists of a frame header followed by the actual frame data
	# frame header (10 bytes in v2.3 and v2.4)
	# frame id: 4 bytes - unique identifier eg. TIT2 (Title), TPE1 (Artist)
	# size:     4 bytes - the size of the data part of the frame, excluding 10 byte header
	# flags:    2 bytes - indicators of compression, encryption, or read-only status

	frames = {}
	offset = 0
	length = len(data)

	while offset + 10 <= length:
		header = data[offset:offset + 10]

		if header.strip(b"\x00") == b"":
			break

		frame_id = header[:4].decode("latin1")
		size_bytes = header[4:8]
		if version == 4:
			size = decode_int(size_bytes, synchsafe=True)
		else:
			size = decode_int(size_bytes, synchsafe=False)

		frame_data = data[offset + 10: offset + 10 + size]
		if frame_id.startswith("T"):
			frames[frame_id] = decode_text(frame_data)
		else:
			frames[frame_id] = frame_data

		offset += 10 + size

	return frames
