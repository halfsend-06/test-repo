"""File saving module with correct UTF-8 buffer sizing.

Fixed in v2.3.2: buffer allocation now uses byte length instead of
character count, preventing overflow when multibyte UTF-8 characters
cause the encoded size to exceed the character-count-based estimate.
"""

BUFFER_SIZE = 65536  # 64KB


def _compute_buffer_size(data: bytes) -> int:
    """Return a buffer size large enough to hold *data*.

    The buffer is the smallest multiple of BUFFER_SIZE that is >= len(data).
    Using byte length (not character count) ensures multibyte UTF-8
    sequences are accounted for.
    """
    length = len(data)
    if length == 0:
        return BUFFER_SIZE
    return ((length - 1) // BUFFER_SIZE + 1) * BUFFER_SIZE


def save_file(path: str, content: str) -> None:
    """Save *content* to *path* with correct buffer sizing.

    The content is encoded as UTF-8.  The write buffer is sized from
    the encoded byte length so that multibyte characters do not cause
    an overflow.
    """
    encoded = content.encode("utf-8")
    buf_size = _compute_buffer_size(encoded)
    buf = bytearray(buf_size)
    buf[: len(encoded)] = encoded

    with open(path, "wb") as fh:
        fh.write(buf[: len(encoded)])
