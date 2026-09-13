"""File I/O module for saving documents.

Handles document serialization with proper UTF-8 encoding support,
including multibyte characters (emoji, CJK, etc.) at any file size.
"""

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

    with open(filepath, "wb") as f:
        offset = 0
        while offset < byte_length:
            chunk = encoded[offset : offset + BUFFER_SIZE]
            f.write(chunk)
            offset += len(chunk)
