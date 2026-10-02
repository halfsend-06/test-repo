"""File saving module with correct UTF-8 buffer allocation.

Provides file-saving functionality that allocates buffers based on
byte length rather than character count, preventing buffer overflows
when the text contains multibyte UTF-8 characters (e.g. emoji or CJK).
"""

_BUFFER_SIZE = 65536  # 64KB in bytes


def save_file(path: str, content: str) -> None:
    """Save content to a file, chunking by byte length.

    Encodes the full string to UTF-8 first, then writes in
    ``_BUFFER_SIZE``-byte chunks. This avoids the v2.3.1 regression
    where the buffer was sized by *character* count, causing an
    overflow when multibyte characters made the byte payload exceed
    the allocated buffer.

    Args:
        path: Destination file path.
        content: Text content to write.
    """
    encoded = content.encode("utf-8")

    with open(path, "wb") as fh:
        offset = 0
        total = len(encoded)
        while offset < total:
            end = min(offset + _BUFFER_SIZE, total)
            fh.write(encoded[offset:end])
            offset = end
