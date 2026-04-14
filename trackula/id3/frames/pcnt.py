from ...frame import PlayCountFrame


def parse_play_count(frame_id: str, data: bytes) -> PlayCountFrame:
    # PCNT is just a big-endian integer, minimum 4 bytes, extensible.
    count = int.from_bytes(data, "big") if data else 0
    return PlayCountFrame(frame_id=frame_id, count=count)


def build_play_count(frame: PlayCountFrame) -> bytes:
    if frame.count == 0:
        return b"\x00\x00\x00\x00"
    count_len = max(4, (frame.count.bit_length() + 7) // 8)
    return frame.count.to_bytes(count_len, "big")
