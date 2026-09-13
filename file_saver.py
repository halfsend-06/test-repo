"""File save module with correct UTF-8 multibyte character handling.

Fixes a segmentation fault that occurred when saving files larger than
64KB containing UTF-8 multibyte characters (e.g., emoji or CJK characters).
The bug was caused by allocating the write buffer based on character count
rather than byte length, which caused a buffer overflow when multibyte
characters pushed the actual byte size beyond the allocated buffer.
"""

import os
import stat
import tempfile

# Prior to the fix, the save path used a fixed 64KB buffer and calculated
# required size from len(text) (character count). For multibyte UTF-8
# characters, the byte length can be up to 4x the character count, causing
# a buffer overflow when the byte representation exceeded 64KB.
CHUNK_SIZE = 64 * 1024  # 64KB write chunks


def save_file(path: str, content: str) -> None:
    """Save content to a file with proper UTF-8 encoding.

    Uses byte-length-aware buffering to avoid overflow when content
    contains multibyte UTF-8 characters. Writes atomically via a
    temporary file to prevent data loss on failure.

    Args:
        path: Destination file path.
        content: Text content to save (may contain multibyte UTF-8 chars).

    Raises:
        OSError: If the file cannot be written.
        TypeError: If content is not a string.
    """
    if not isinstance(content, str):
        raise TypeError(f"content must be str, got {type(content).__name__}")

    # Encode to bytes first so buffer size reflects actual byte length,
    # not character count. This is the core fix: the old code used
    # len(content) (character count) to decide whether to chunk, but
    # multibyte characters mean byte_length > character_count.
    data = content.encode("utf-8")

    abs_path = os.path.abspath(path)
    dir_name = os.path.dirname(abs_path)
    os.makedirs(dir_name, exist_ok=True)

    # Capture existing file permissions so we can restore them after
    # the atomic replace (mkstemp creates files with 0o600).
    original_mode = None
    try:
        original_mode = stat.S_IMODE(os.stat(abs_path).st_mode)
    except FileNotFoundError:
        pass

    # Write atomically: write to a temp file in the same directory,
    # then rename. This prevents partial writes on crash.
    fd, tmp_path = tempfile.mkstemp(dir=dir_name, prefix=".save_")
    try:
        offset = 0
        while offset < len(data):
            chunk = data[offset : offset + CHUNK_SIZE]
            written = os.write(fd, chunk)
            offset += written
        os.fsync(fd)
        os.close(fd)
        fd = -1  # Mark as closed
        os.replace(tmp_path, abs_path)
        if original_mode is not None:
            os.chmod(abs_path, original_mode)
    except BaseException:
        if fd >= 0:
            os.close(fd)
        # Clean up temp file on failure
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def load_file(path: str) -> str:
    """Load a UTF-8 encoded file and return its content as a string.

    Args:
        path: File path to read.

    Returns:
        The file content as a string.

    Raises:
        FileNotFoundError: If the file does not exist.
        OSError: If the file cannot be read.
    """
    with open(path, "r", encoding="utf-8") as f:
        return f.read()
