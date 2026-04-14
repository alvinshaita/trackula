from ...frame import PopularimeterFrame


def parse_popularimeter(frame_id: str, data: bytes) -> PopularimeterFrame:
    # POPM structure:
    #   Email to user   latin-1, null-terminated
    #   Rating          1 byte (0 = unknown, 1..255 = rating)
    #   Counter         4+ bytes big-endian, extensible
    email_end = data.index(b"\x00")
    email = data[:email_end].decode("latin1")
    rating = data[email_end + 1]

    counter_bytes = data[email_end + 2:]
    counter = int.from_bytes(counter_bytes, "big") if counter_bytes else 0

    return PopularimeterFrame(
        frame_id=frame_id,
        email=email,
        rating=rating,
        counter=counter,
    )


def build_popularimeter(frame: PopularimeterFrame) -> bytes:
    out = frame.email.encode("latin1") + b"\x00" + bytes([frame.rating])

    # Counter is a minimum of 4 bytes, but can be larger if needed.
    if frame.counter == 0:
        counter_bytes = b"\x00\x00\x00\x00"
    else:
        counter_len = max(4, (frame.counter.bit_length() + 7) // 8)
        counter_bytes = frame.counter.to_bytes(counter_len, "big")

    return out + counter_bytes
