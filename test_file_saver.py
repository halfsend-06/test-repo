"""Tests for file_saver module.

Verifies that file saving correctly handles UTF-8 multibyte characters
at various size boundaries, particularly around the 64KB threshold.
"""

import os
import tempfile

import pytest

from file_saver import BUFFER_SIZE, load_file, save_file


@pytest.fixture
def tmp_path_file(tmp_path):
    """Return a temporary file path for test output."""
    return str(tmp_path / "test_output.txt")


class TestSaveFile:
    """Tests for the save_file function."""

    def test_small_ascii_file(self, tmp_path_file):
        """ASCII file under 64KB saves correctly."""
        content = "Hello, world!\n" * 100
        save_file(tmp_path_file, content)
        assert load_file(tmp_path_file) == content

    def test_64kb_ascii_file(self, tmp_path_file):
        """Exactly 64KB ASCII file saves correctly."""
        content = "A" * BUFFER_SIZE
        save_file(tmp_path_file, content)
        assert load_file(tmp_path_file) == content

    def test_over_64kb_ascii_file(self, tmp_path_file):
        """ASCII file over 64KB saves correctly."""
        content = "B" * (BUFFER_SIZE + 1024)
        save_file(tmp_path_file, content)
        assert load_file(tmp_path_file) == content

    def test_small_multibyte_file(self, tmp_path_file):
        """Small file with multibyte UTF-8 characters saves correctly."""
        content = "\U0001f600" * 100  # 😀 emoji (4 bytes each)
        save_file(tmp_path_file, content)
        assert load_file(tmp_path_file) == content

    def test_over_64kb_emoji_file(self, tmp_path_file):
        """File with emoji where byte count exceeds 64KB saves correctly.

        This is the primary regression test for issue #59. Each emoji is
        4 bytes in UTF-8, so 20000 emoji = 80KB in bytes but only 20000
        characters.
        """
        content = "\U0001f600" * 20000  # 80KB of emoji
        assert len(content) < BUFFER_SIZE  # char count under 64K
        assert len(content.encode("utf-8")) > BUFFER_SIZE  # byte count over 64K
        save_file(tmp_path_file, content)
        result = load_file(tmp_path_file)
        assert result == content

    def test_over_64kb_cjk_file(self, tmp_path_file):
        """File with CJK characters where byte count exceeds 64KB saves correctly."""
        # CJK characters are 3 bytes each in UTF-8
        content = "\u4e16" * 25000  # 75KB of CJK (世)
        assert len(content.encode("utf-8")) > BUFFER_SIZE
        save_file(tmp_path_file, content)
        assert load_file(tmp_path_file) == content

    def test_mixed_ascii_and_multibyte_over_64kb(self, tmp_path_file):
        """Mixed ASCII and multibyte content over 64KB saves correctly."""
        ascii_part = "Hello " * 5000  # 30KB ASCII
        emoji_part = "\U0001f680" * 10000  # 40KB emoji
        content = ascii_part + emoji_part
        assert len(content.encode("utf-8")) > BUFFER_SIZE
        save_file(tmp_path_file, content)
        assert load_file(tmp_path_file) == content

    def test_char_count_under_64k_byte_count_over(self, tmp_path_file):
        """Dense multibyte: char count < 64K but byte count > 64KB.

        This directly targets the root cause of issue #59 where
        buffer was sized by character count instead of byte length.
        """
        # 4-byte emoji: 16384 chars = 65536 bytes (exactly 64KB)
        # Use 16385 chars = 65540 bytes (just over 64KB)
        content = "\U0001f4a9" * 16385
        assert len(content) < BUFFER_SIZE
        assert len(content.encode("utf-8")) > BUFFER_SIZE
        save_file(tmp_path_file, content)
        assert load_file(tmp_path_file) == content

    def test_roundtrip_preserves_content(self, tmp_path_file):
        """Saved and loaded content matches exactly (round-trip)."""
        content = "ASCII text \u00e9\u00e8\u00ea \U0001f600\U0001f680 \u4e16\u754c\n" * 5000
        save_file(tmp_path_file, content)
        assert load_file(tmp_path_file) == content

    def test_empty_file(self, tmp_path_file):
        """Empty content saves correctly."""
        save_file(tmp_path_file, "")
        assert load_file(tmp_path_file) == ""

    def test_file_bytes_on_disk(self, tmp_path_file):
        """Verify the on-disk size matches expected byte length."""
        content = "\U0001f600" * 20000  # 80000 bytes
        save_file(tmp_path_file, content)
        assert os.path.getsize(tmp_path_file) == len(content.encode("utf-8"))
