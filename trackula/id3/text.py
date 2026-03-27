def encode_text(text: str, encoding: int = 3):
	if encoding == 0:
		return b"\x00" + text.encode("latin1")
	elif encoding == 1:
		return b"\x01" + text.encode("utf-16")
	else:
		return b"\x03" + text.encode("utf-8")


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
