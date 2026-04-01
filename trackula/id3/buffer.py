def decode_synchsafe(data: bytes) -> int:
	size = 0
	for b in data:
		size = (size << 7) | (b & 0x7F)
	return size


def encode_synchsafe(size: int) -> bytes:
	data = bytearray(4)
	for i in range(4)[::-1]:
		data[i] = size & 0x7F
		size >>= 7
	return bytes(data)


def decode_int(size: int, synchsafe: bool) -> int:
	if synchsafe:
		return decode_synchsafe(size)
	else:
		return int.from_bytes(size, byteorder="big")


def encode_int(size: int, synchsafe: bool) -> bytes:
	if synchsafe:
		return encode_synchsafe(size)
	else:
		return len(size).to_bytes(4, "big")
