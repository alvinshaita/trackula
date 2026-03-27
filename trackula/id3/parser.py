from .buffer import decode_synchsafe

def parse_id3(data: bytes):
	header = parse_header(data[:10])
	
	body = data[10:10+header["size"]]
	frames = parse_frames(body)

	return {
		"header": header,
		"frames": frames,
	}


def parse_header(data: bytes):
	# main header is always 10 bytes long
	# in ID3v2, header is located at the beginning of the file
	# identifier: 3 bytes - always "ID3"
	# version: 	  2 bytes - major version and revision eg. 03 00 for v2.3.0
	# flags:      1 byte - bitwise indicator
	# size:       4 bytes - total size of the tag, excluding 10 byte header

	if data[:3] != b"ID3":
		raise Exception("Missing ID3 identifier")

	version = data[3]
	revision = data[4]
	flags = data[5]
	size = decode_synchsafe(data[6:10])

	return {
		"version": version,
		"revision": revision,
		"flags": flags,
		"size": size,
	}


def parse_frames(data: bytes):
	# each frame consists of a frame header followed by the actual frame data
	# frame header (10 bytes in v2.3 and v2.4)
	# frame id: 4 bytes - unique identifier eg. TIT2 (Title), TPE1 (Artist)
	# size: 4 bytes - the size of the data part of the frame, excluding 10 byte header
	# flags: 2 bytes - indicators of compression, encryption, or read-only status

	frames = {}
	offset = 0
	length = len(data)

	while offset + 10 <= length:
		header = data[offset:offset + 10]

		if header.strip(b"\x00") == b"":
			break

		frame_id = header[:4].decode("latin1")
		size = int.from_bytes(header[4:8], "big")

		frame_data = data[offset + 10: offset + 10 + size]

		if frame_id.startswith("T"):
			frames[frame_id] = decode_text(frame_data)
		else:
			frames[frame_id] = frame_data

		offset += 10 + size

	return frames


def decode_text(data: bytes):
	# decode ID3 text frame payload
	# first byte = encoding

	encoding = data[0]
	payload = data[1:]

	if encoding == 0:
		return payload.decode("latin1")
	elif encoding == 1:
		return payload.decode("utf-16")
	elif encoding == 3:
		return payload.decode("utf-8")
	else:
		return payload.decode("latin1")
