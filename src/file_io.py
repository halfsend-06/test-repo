"""File I/O module for saving documents.

Handles document serialization with proper UTF-8 encoding support,
including multibyte characters (emoji, CJK, etc.) at any file size.
"""

import os
import tempfile

# Buffer size threshold for chunked writes (64KB)
BUFFER_SIZE = 65536


def save_file(content: str, filepath: str) -> None:
    """Save content to a file with proper UTF-8 encoding.

    Uses byte-length calculation for buffer allocation to correctly
    handle multibyte UTF-8 characters at any file size.

    Args:
        content: The text content to save.
        filepath: Destination file path.

    Raises:
        OSError: If the file cannot be written.
    """
    encoded = content.encode("utf-8")
    byte_length = len(encoded)

    # Write atomically via a temp file to avoid partial writes on crash
    dir_name = os.path.dirname(os.path.abspath(filepath))
    fd, tmp_path = tempfile.mkstemp(dir=dir_name)
    try:
        offset = 0
        while offset < byte_length:
            chunk = encoded[offset : offset + BUFFER_SIZE]
            os.write(fd, chunk)
            offset += len(chunk)
        os.close(fd)
        os.replace(tmp_path, filepath)
    except BaseException:
        os.close(fd)
        os.unlink(tmp_path)
        raise
