"""Tests for the file_saver module.

Covers the buffer-overflow regression (issue #1888): saving files larger
than 64KB that contain UTF-8 multibyte characters must succeed without
data corruption.
"""

import os
import tempfile

from src.file_saver import BUFFER_SIZE, _compute_buffer_size, save_file


class TestComputeBufferSize:
    """Unit tests for _compute_buffer_size."""

    def test_empty_data(self):
        assert _compute_buffer_size(b"") == BUFFER_SIZE

    def test_under_one_buffer(self):
        data = b"x" * 100
        assert _compute_buffer_size(data) == BUFFER_SIZE

    def test_exactly_one_buffer(self):
        data = b"x" * BUFFER_SIZE
        assert _compute_buffer_size(data) == BUFFER_SIZE

    def test_one_byte_over(self):
        data = b"x" * (BUFFER_SIZE + 1)
        assert _compute_buffer_size(data) == BUFFER_SIZE * 2

    def test_large_multibyte_content(self):
        # Emoji U+1F600 is 4 bytes in UTF-8
        text = "\U0001f600" * (BUFFER_SIZE // 2)
        encoded = text.encode("utf-8")
        # Character count < BUFFER_SIZE but byte length > BUFFER_SIZE
        assert len(text) < BUFFER_SIZE
        assert len(encoded) > BUFFER_SIZE
        buf = _compute_buffer_size(encoded)
        assert buf >= len(encoded)


class TestSaveFile:
    """Integration tests for save_file."""

    def _roundtrip(self, content: str) -> str:
        """Save content to a temp file and read it back."""
        fd, path = tempfile.mkstemp()
        os.close(fd)
        try:
            save_file(path, content)
            with open(path, "rb") as fh:
                return fh.read().decode("utf-8")
        finally:
            os.unlink(path)

    def test_small_ascii_file(self):
        content = "hello world"
        assert self._roundtrip(content) == content

    def test_small_multibyte_file(self):
        content = "hello \U0001f600 world"
        assert self._roundtrip(content) == content

    def test_large_ascii_file_over_64kb(self):
        content = "A" * (BUFFER_SIZE + 1024)
        assert self._roundtrip(content) == content

    def test_large_multibyte_file_just_under_64kb_chars(self):
        """File just under 64KB in character count but over in byte length."""
        # Each emoji is 4 bytes; 20000 emojis = 80000 bytes > 64KB
        content = "\U0001f600" * 20000
        assert len(content) < BUFFER_SIZE
        assert len(content.encode("utf-8")) > BUFFER_SIZE
        assert self._roundtrip(content) == content

    def test_large_multibyte_file_over_64kb(self):
        """File over 64KB containing emoji characters (the crash scenario)."""
        # ~70KB of emoji text: 18000 emojis * 4 bytes = 72000 bytes
        content = "\U0001f600" * 18000
        assert self._roundtrip(content) == content

    def test_mixed_ascii_and_multibyte_over_64kb(self):
        """Mixed ASCII and multibyte content well over 64KB."""
        ascii_part = "A" * 40000
        emoji_part = "\U0001f600" * 10000  # 40000 bytes
        content = ascii_part + emoji_part
        assert len(content.encode("utf-8")) > BUFFER_SIZE
        assert self._roundtrip(content) == content

    def test_cjk_characters_over_64kb(self):
        """CJK characters (3 bytes each in UTF-8) over 64KB."""
        content = "世" * 25000  # 75000 bytes
        assert len(content.encode("utf-8")) > BUFFER_SIZE
        assert self._roundtrip(content) == content

    def test_byte_integrity(self):
        """Verify byte-level integrity of saved content."""
        content = "ASCII \U0001f600 世界 more text \U0001f680" * 5000
        fd, path = tempfile.mkstemp()
        os.close(fd)
        try:
            save_file(path, content)
            with open(path, "rb") as fh:
                raw = fh.read()
            assert raw == content.encode("utf-8")
        finally:
            os.unlink(path)
