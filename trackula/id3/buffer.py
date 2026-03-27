def decode_synchsafe(data: bytes) -> int:
	size = 0
	for b in data:
		size = (size << 7) | (b & 0x7F)
	return size
