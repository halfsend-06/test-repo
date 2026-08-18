"""Tests for the file save module.

Covers the fix for issue #1632: segfault when saving files larger
than 64KB that contain UTF-8 multibyte characters.
"""

import os
import tempfile

from src.file_save import BUFFER_SIZE, _calculate_byte_length, save_file


class TestCalculateByteLength:
    """Verify byte-length calculation for various character types."""

    def test_ascii_only(self):
        text = "a" * 100
        assert _calculate_byte_length(text) == 100

    def test_multibyte_emoji(self):
        # Each emoji is 4 bytes in UTF-8.
        text = "\U0001f600" * 10  # 😀 x10
        assert _calculate_byte_length(text) == 40

    def test_cjk_characters(self):
        # Each CJK character is 3 bytes in UTF-8.
        text = "世界" * 10  # 世界 x10
        assert _calculate_byte_length(text) == 60

    def test_mixed_content(self):
        text = "hello\U0001f600世"
        # 5 ASCII (5 bytes) + 1 emoji (4 bytes) + 1 CJK (3 bytes) = 12
        assert _calculate_byte_length(text) == 12


class TestSaveFile:
    """Verify file saving with various sizes and encodings."""

    def _round_trip(self, content):
        """Write content via save_file, read it back, return the result."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
            path = tmp.name
        try:
            save_file(path, content)
            with open(path, "rb") as fh:
                return fh.read().decode("utf-8")
        finally:
            os.unlink(path)

    # -- ASCII files -------------------------------------------------------

    def test_ascii_under_buffer(self):
        content = "a" * (BUFFER_SIZE - 1)
        assert self._round_trip(content) == content

    def test_ascii_over_buffer(self):
        content = "a" * (BUFFER_SIZE + 1024)
        assert self._round_trip(content) == content

    # -- Multibyte UTF-8 files ---------------------------------------------

    def test_multibyte_utf8_under_buffer(self):
        # ~60KB of emoji (each 4 bytes) → under 64KB in bytes.
        count = (BUFFER_SIZE // 4) - 100
        content = "\U0001f600" * count
        assert self._round_trip(content) == content

    def test_multibyte_utf8_over_buffer(self):
        """Core regression test for #1632.

        A file whose character count is below 64K but whose UTF-8 byte
        length exceeds 64KB must save without crashing.
        """
        # 20_000 emoji characters × 4 bytes = 80KB (> 64KB buffer).
        content = "\U0001f600" * 20_000
        assert len(content) < BUFFER_SIZE  # chars fit in old buffer
        assert len(content.encode("utf-8")) > BUFFER_SIZE  # bytes do not
        assert self._round_trip(content) == content

    def test_cjk_over_buffer(self):
        # 25_000 CJK characters × 3 bytes = 75KB (> 64KB buffer).
        content = "世" * 25_000
        assert self._round_trip(content) == content

    # -- Mixed content files -----------------------------------------------

    def test_mixed_ascii_and_multibyte_over_buffer(self):
        ascii_part = "x" * (BUFFER_SIZE // 2)
        emoji_part = "\U0001f600" * (BUFFER_SIZE // 4)
        content = ascii_part + emoji_part
        assert len(content.encode("utf-8")) > BUFFER_SIZE
        assert self._round_trip(content) == content

    # -- Edge cases --------------------------------------------------------

    def test_empty_file(self):
        assert self._round_trip("") == ""

    def test_exact_buffer_boundary_ascii(self):
        content = "a" * BUFFER_SIZE
        assert self._round_trip(content) == content

    def test_multibyte_at_chunk_boundary(self):
        """Ensure a multibyte character that straddles a chunk boundary
        does not get split incorrectly."""
        # Fill almost exactly one buffer with ASCII, then add emoji.
        content = "a" * (BUFFER_SIZE - 1) + "\U0001f600"
        assert self._round_trip(content) == content
