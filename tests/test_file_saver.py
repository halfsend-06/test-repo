"""Tests for the file_saver module.

Covers the buffer-overflow regression (issue #1888): saving files larger
than 64KB that contain UTF-8 multibyte characters must succeed without
data corruption.
"""

import os
import tempfile
import unittest

from src.file_saver import BUFFER_SIZE, _compute_buffer_size, save_file


class TestComputeBufferSize(unittest.TestCase):
    """Unit tests for _compute_buffer_size."""

    def test_empty_data(self):
        self.assertEqual(_compute_buffer_size(b""), BUFFER_SIZE)

    def test_under_one_buffer(self):
        data = b"x" * 100
        self.assertEqual(_compute_buffer_size(data), BUFFER_SIZE)

    def test_exactly_one_buffer(self):
        data = b"x" * BUFFER_SIZE
        self.assertEqual(_compute_buffer_size(data), BUFFER_SIZE)

    def test_one_byte_over(self):
        data = b"x" * (BUFFER_SIZE + 1)
        self.assertEqual(_compute_buffer_size(data), BUFFER_SIZE * 2)

    def test_large_multibyte_content(self):
        # Emoji U+1F600 is 4 bytes in UTF-8
        text = "\U0001f600" * (BUFFER_SIZE // 2)
        encoded = text.encode("utf-8")
        # Character count < BUFFER_SIZE but byte length > BUFFER_SIZE
        self.assertLess(len(text), BUFFER_SIZE)
        self.assertGreater(len(encoded), BUFFER_SIZE)
        buf = _compute_buffer_size(encoded)
        self.assertGreaterEqual(buf, len(encoded))


class TestSaveFile(unittest.TestCase):
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

    def test_empty_content(self):
        """Saving empty content writes an empty file."""
        self.assertEqual(self._roundtrip(""), "")

    def test_small_ascii_file(self):
        content = "hello world"
        self.assertEqual(self._roundtrip(content), content)

    def test_small_multibyte_file(self):
        content = "hello \U0001f600 world"
        self.assertEqual(self._roundtrip(content), content)

    def test_large_ascii_file_over_64kb(self):
        content = "A" * (BUFFER_SIZE + 1024)
        self.assertEqual(self._roundtrip(content), content)

    def test_exact_buffer_boundary(self):
        """Content whose UTF-8 encoding is exactly 65536 bytes."""
        content = "A" * BUFFER_SIZE
        self.assertEqual(len(content.encode("utf-8")), BUFFER_SIZE)
        self.assertEqual(self._roundtrip(content), content)

    def test_large_multibyte_file_just_under_64kb_chars(self):
        """File just under 64KB in character count but over in byte length."""
        # Each emoji is 4 bytes; 20000 emojis = 80000 bytes > 64KB
        content = "\U0001f600" * 20000
        self.assertLess(len(content), BUFFER_SIZE)
        self.assertGreater(len(content.encode("utf-8")), BUFFER_SIZE)
        self.assertEqual(self._roundtrip(content), content)

    def test_large_multibyte_file_over_64kb(self):
        """File over 64KB containing emoji characters (the crash scenario)."""
        # ~70KB of emoji text: 18000 emojis * 4 bytes = 72000 bytes
        content = "\U0001f600" * 18000
        self.assertEqual(self._roundtrip(content), content)

    def test_mixed_ascii_and_multibyte_over_64kb(self):
        """Mixed ASCII and multibyte content well over 64KB."""
        ascii_part = "A" * 40000
        emoji_part = "\U0001f600" * 10000  # 40000 bytes
        content = ascii_part + emoji_part
        self.assertGreater(len(content.encode("utf-8")), BUFFER_SIZE)
        self.assertEqual(self._roundtrip(content), content)

    def test_cjk_characters_over_64kb(self):
        """CJK characters (3 bytes each in UTF-8) over 64KB."""
        content = "世" * 25000  # 75000 bytes
        self.assertGreater(len(content.encode("utf-8")), BUFFER_SIZE)
        self.assertEqual(self._roundtrip(content), content)

    def test_byte_integrity(self):
        """Verify byte-level integrity of saved content."""
        content = "ASCII \U0001f600 世界 more text \U0001f680" * 5000
        fd, path = tempfile.mkstemp()
        os.close(fd)
        try:
            save_file(path, content)
            with open(path, "rb") as fh:
                raw = fh.read()
            self.assertEqual(raw, content.encode("utf-8"))
        finally:
            os.unlink(path)
