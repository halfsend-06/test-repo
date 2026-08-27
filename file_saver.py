"""File save module with correct UTF-8 buffer handling.

This module provides file save functionality that correctly allocates
buffers based on byte length rather than character count, preventing
buffer overflows when saving files containing multibyte UTF-8 characters
(e.g., emoji, CJK characters) that exceed 64KB.
"""

# Buffer size threshold in bytes
BUFFER_SIZE = 65536  # 64KB


def save_file(path: str, content: str) -> None:
    """Save content to a file, correctly handling multibyte UTF-8.

    Allocates the write buffer based on the encoded byte length of the
    content rather than the character count, ensuring files with multibyte
    UTF-8 characters are saved correctly regardless of size.

    Args:
        path: Destination file path.
        content: Text content to save.

    Raises:
        OSError: If the file cannot be written.
    """
    encoded = content.encode("utf-8")
    byte_length = len(encoded)

    # Allocate buffer based on byte length, not character count.
    # Previous implementation used len(content) (character count) which
    # caused a buffer overflow when multibyte characters pushed the byte
    # length past 64KB while the character count remained below it.
    buf = bytearray(byte_length)
    buf[:byte_length] = encoded

    with open(path, "wb") as f:
        f.write(buf)


def load_file(path: str) -> str:
    """Load a file and return its text content.

    Args:
        path: Source file path.

    Returns:
        The decoded text content of the file.

    Raises:
        FileNotFoundError: If the file does not exist.
        OSError: If the file cannot be read.
    """
    with open(path, "rb") as f:
        return f.read().decode("utf-8")
