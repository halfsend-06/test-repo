"""File save module.

Handles writing document content to disk with proper encoding support.
"""

# Default buffer size for chunked file writes.
BUFFER_SIZE = 65536  # 64KB


def _calculate_byte_length(text):
    """Return the byte length of text when encoded as UTF-8.

    This must be used instead of len(text) when allocating write
    buffers, because multibyte UTF-8 characters (emoji, CJK, etc.)
    occupy more than one byte per character.
    """
    return len(text.encode("utf-8"))


def save_file(path, content):
    """Save content to a file at the given path.

    The content is written in chunks whose size is determined by the
    byte length of the data, not the character count.  Prior to v2.3.1
    the chunk size was calculated from ``len(content)`` (character
    count), which caused a buffer overrun when multibyte UTF-8
    characters pushed the encoded size past the 64KB buffer boundary.

    Args:
        path: Destination file path.
        content: Unicode string to write.

    Raises:
        OSError: If the file cannot be opened or written.
    """
    encoded = content.encode("utf-8")
    byte_length = len(encoded)

    with open(path, "wb") as fh:
        offset = 0
        while offset < byte_length:
            end = min(offset + BUFFER_SIZE, byte_length)
            fh.write(encoded[offset:end])
            offset = end
