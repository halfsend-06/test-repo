"""File saving module with correct UTF-8 buffer allocation.

This module provides file-saving functionality that correctly handles
UTF-8 multibyte characters by allocating buffers based on byte length
rather than character count.
"""

import os

# Buffer size threshold in bytes.
BUFFER_SIZE = 65536  # 64KB


def _byte_length(data: str) -> int:
    """Return the byte length of a string when encoded as UTF-8."""
    return len(data.encode("utf-8"))


def save_file(path: str, content: str) -> None:
    """Save content to a file, handling UTF-8 multibyte characters correctly.

    The content is written in chunks whose size is determined by byte
    length, not character count.  This prevents buffer overflows when
    the text contains multibyte UTF-8 characters (e.g. emoji or CJK)
    that cause the byte representation to exceed the buffer boundary.

    Args:
        path: Destination file path.
        content: Text content to write.
    """
    encoded = content.encode("utf-8")
    dir_name = os.path.dirname(path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)

    with open(path, "wb") as fh:
        offset = 0
        total = len(encoded)
        while offset < total:
            end = min(offset + BUFFER_SIZE, total)
            fh.write(encoded[offset:end])
            offset = end


def read_file(path: str) -> str:
    """Read a UTF-8 encoded file and return its contents as a string.

    Args:
        path: Source file path.

    Returns:
        The decoded text content of the file.
    """
    with open(path, "rb") as fh:
        return fh.read().decode("utf-8")
