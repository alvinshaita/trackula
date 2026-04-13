def encode_text(text: str, encoding: int = 3) -> bytes:
    if encoding == 0:
        return b"\x00" + text.encode("latin1")
    elif encoding == 1:
        return b"\x01" + text.encode("utf-16")
    else:
        return b"\x03" + text.encode("utf-8")


def decode_text(data: bytes) -> str:
    # decode ID3 text frame payload
    # first byte = encoding
    encoding = data[0]
    payload = data[1:]
    return decode_by_encoding(payload, encoding)


def decode_by_encoding(data: bytes, encoding: int) -> str:
    """Decode `data` as text using the given ID3 encoding byte value."""
    if encoding == 0:
        return data.decode("latin1")
    elif encoding == 1:
        return data.decode("utf-16")
    elif encoding == 2:
        return data.decode("utf-16-be")
    elif encoding == 3:
        return data.decode("utf-8")
    else:
        return data.decode("latin1")


def encode_by_encoding(text: str, encoding: int) -> bytes:
    """Encode `text` to bytes using the given ID3 encoding byte value."""
    if encoding == 0:
        return text.encode("latin1")
    elif encoding == 1:
        return text.encode("utf-16")
    elif encoding == 2:
        return text.encode("utf-16-be")
    elif encoding == 3:
        return text.encode("utf-8")
    else:
        return text.encode("latin1")


def find_terminator(data: bytes, start: int, encoding: int) -> int:
    """Return the offset of the null terminator in a text field.

    For UTF-16 encodings the terminator is two zero bytes aligned to the
    start offset; for Latin-1 and UTF-8 it's a single zero byte.
    Returns len(data) if no terminator is found.
    """
    if encoding in (1, 2):
        i = start
        while i < len(data) - 1:
            if data[i] == 0 and data[i + 1] == 0 and (i - start) % 2 == 0:
                return i
            i += 1
        return len(data)
    else:
        try:
            return data.index(b"\x00", start)
        except ValueError:
            return len(data)


def terminator_length(encoding: int) -> int:
    return 2 if encoding in (1, 2) else 1
