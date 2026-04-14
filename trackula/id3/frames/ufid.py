from ...frame import UniqueFileIdentifierFrame


def parse_ufid(frame_id: str, data: bytes) -> UniqueFileIdentifierFrame:
    # UFID structure:
    #   Owner identifier  latin-1 URL-shaped string, null-terminated
    #   Identifier        binary, rest of frame (up to 64 bytes per spec)
    owner_end = data.index(b"\x00")
    owner = data[:owner_end].decode("latin1")
    identifier = data[owner_end + 1:]

    return UniqueFileIdentifierFrame(
        frame_id=frame_id,
        owner=owner,
        identifier=identifier,
    )


def build_ufid(frame: UniqueFileIdentifierFrame) -> bytes:
    return frame.owner.encode("latin1") + b"\x00" + frame.identifier
