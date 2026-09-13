"""Tests for the file I/O save path.

Verifies that save_file correctly handles multibyte UTF-8 characters
at sizes above the 64KB buffer threshold, preventing the buffer
overflow that caused the segfault in v2.3.1.
"""

import os
import tempfile

from src.file_io import BUFFER_SIZE, save_file


def test_save_large_ascii_file():
    """Large ASCII-only files save and reload correctly (control case)."""
    content = "A" * (BUFFER_SIZE + 1024)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        path = f.name
    try:
        save_file(content, path)
        with open(path, "r", encoding="utf-8") as f:
            result = f.read()
        assert result == content
    finally:
        os.unlink(path)


def test_save_large_multibyte_file():
    """Files >64KB with multibyte UTF-8 characters save without crash."""
    # Each emoji is 4 bytes in UTF-8; ~18K emoji exceed 64KB in bytes
    emoji_count = (BUFFER_SIZE // 4) + 256
    content = "\U0001f600" * emoji_count  # 😀
    assert len(content.encode("utf-8")) > BUFFER_SIZE

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        path = f.name
    try:
        save_file(content, path)
        with open(path, "r", encoding="utf-8") as f:
            result = f.read()
        assert result == content
    finally:
        os.unlink(path)


def test_save_multibyte_at_buffer_boundary():
    """A multibyte character straddling the 64KB boundary is handled."""
    # Fill up to exactly the buffer size minus 1 byte with ASCII,
    # then add a 4-byte emoji that crosses the boundary.
    ascii_part = "A" * (BUFFER_SIZE - 1)
    content = ascii_part + "\U0001f680"  # 🚀 (4 bytes)
    encoded = content.encode("utf-8")
    assert len(encoded) == BUFFER_SIZE + 3  # 1 byte short + 4-byte char

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        path = f.name
    try:
        save_file(content, path)
        with open(path, "r", encoding="utf-8") as f:
            result = f.read()
        assert result == content
    finally:
        os.unlink(path)


def test_save_large_cjk_file():
    """Files >64KB with CJK characters (3-byte UTF-8) save correctly."""
    # CJK character U+4E16 (世) is 3 bytes in UTF-8
    char_count = (BUFFER_SIZE // 3) + 256
    content = "世" * char_count
    assert len(content.encode("utf-8")) > BUFFER_SIZE

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        path = f.name
    try:
        save_file(content, path)
        with open(path, "r", encoding="utf-8") as f:
            result = f.read()
        assert result == content
    finally:
        os.unlink(path)


def test_save_small_file():
    """Files under the buffer threshold save correctly."""
    content = "Hello, 世界! 🌍"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        path = f.name
    try:
        save_file(content, path)
        with open(path, "r", encoding="utf-8") as f:
            result = f.read()
        assert result == content
    finally:
        os.unlink(path)
