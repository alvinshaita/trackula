# A synchsafe integer uses only 7 bits per byte.
# The first bit is always 0, so each byte contributes only 7 bits
# 0xxxxxxx 0xxxxxxx 0xxxxxxx 0xxxxxxx
# Why synchsafe exists:
#   It avoids accidentally creating this byte: 11111111 (0xFF)
#   MP3 streams use 0xFF as a frame sync marker
#   If your tag size accidentally contains 0xFF, it can confuse MP3 decoders
# Synchsafe ensures: No byte will ever look like an MP3 frame sync


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


def decode_int(size, synchsafe: bool) -> int:
    if synchsafe:
        return decode_synchsafe(size)
    else:
        return int.from_bytes(size, byteorder="big")


def encode_int(size: int, synchsafe: bool) -> bytes:
    if synchsafe:
        return encode_synchsafe(size)
    else:
        return len(size).to_bytes(4, "big")
