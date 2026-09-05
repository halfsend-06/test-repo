"""Tests for file_saver module.

Covers the UTF-8 multibyte save bug: files over 64KB with multibyte
characters must save and round-trip correctly.
"""

import os
import tempfile

import pytest

from file_saver import load_file, save_file


@pytest.fixture()
def tmp_dir():
    """Provide a temporary directory that is cleaned up after the test."""
    with tempfile.TemporaryDirectory() as d:
        yield d


class TestSaveFileUTF8:
    """Tests for the UTF-8 buffer overflow fix."""

    def test_small_file_with_multibyte(self, tmp_dir):
        """File under 64KB with multibyte UTF-8 chars saves successfully."""
        # Each emoji is 4 bytes in UTF-8; 1000 emojis = 4000 bytes < 64KB
        content = "\U0001f600" * 1000
        path = os.path.join(tmp_dir, "small_emoji.txt")

        save_file(path, content)
        assert load_file(path) == content

    def test_large_file_with_multibyte(self, tmp_dir):
        """File over 64KB with multibyte UTF-8 chars saves successfully.

        This is the primary regression test for the reported crash.
        """
        # 70KB worth of 4-byte emoji characters
        # 70 * 1024 / 4 = 17920 characters, but 71680 bytes
        num_chars = (70 * 1024) // 4
        content = "\U0001f600" * num_chars
        byte_len = len(content.encode("utf-8"))
        assert byte_len > 64 * 1024, "Test content must exceed 64KB in bytes"

        path = os.path.join(tmp_dir, "large_emoji.txt")
        save_file(path, content)
        assert load_file(path) == content

    def test_large_file_ascii_only(self, tmp_dir):
        """File over 64KB with ASCII-only content saves successfully."""
        content = "A" * (70 * 1024)
        path = os.path.join(tmp_dir, "large_ascii.txt")

        save_file(path, content)
        assert load_file(path) == content

    def test_multibyte_spanning_chunk_boundary(self, tmp_dir):
        """Multibyte char at the exact 64KB chunk boundary saves correctly.

        Ensures the chunking logic does not split in the middle of a
        multibyte sequence — we encode to bytes first, so chunks are
        always on byte boundaries within the already-encoded data.
        """
        # Fill up to just under 64KB with ASCII, then add emoji
        ascii_part = "X" * (64 * 1024 - 1)
        # Add multibyte characters that push past the boundary
        emoji_part = "\U0001f600" * 100  # 400 bytes
        content = ascii_part + emoji_part

        byte_len = len(content.encode("utf-8"))
        assert byte_len > 64 * 1024

        path = os.path.join(tmp_dir, "boundary.txt")
        save_file(path, content)
        assert load_file(path) == content

    def test_round_trip_cjk_characters(self, tmp_dir):
        """CJK characters (3-byte UTF-8) round-trip correctly over 64KB."""
        # CJK char U+4E00 is 3 bytes in UTF-8
        num_chars = (70 * 1024) // 3
        content = "一" * num_chars
        byte_len = len(content.encode("utf-8"))
        assert byte_len > 64 * 1024

        path = os.path.join(tmp_dir, "large_cjk.txt")
        save_file(path, content)
        assert load_file(path) == content

    def test_mixed_ascii_and_multibyte(self, tmp_dir):
        """Mixed ASCII and multibyte content over 64KB saves correctly."""
        # Alternate ASCII and emoji to create mixed content > 64KB
        unit = "Hello \U0001f600 World 世界 "  # mixed ASCII + emoji + CJK
        repetitions = (70 * 1024) // len(unit.encode("utf-8")) + 1
        content = unit * repetitions
        byte_len = len(content.encode("utf-8"))
        assert byte_len > 64 * 1024

        path = os.path.join(tmp_dir, "mixed.txt")
        save_file(path, content)
        assert load_file(path) == content


class TestSaveFileEdgeCases:
    """Edge case tests for save_file."""

    def test_empty_content(self, tmp_dir):
        """Empty string saves and loads correctly."""
        path = os.path.join(tmp_dir, "empty.txt")
        save_file(path, "")
        assert load_file(path) == ""

    def test_creates_parent_directories(self, tmp_dir):
        """Parent directories are created if they don't exist."""
        path = os.path.join(tmp_dir, "a", "b", "c", "file.txt")
        save_file(path, "test")
        assert load_file(path) == "test"

    def test_overwrites_existing_file(self, tmp_dir):
        """Existing file is overwritten with new content."""
        path = os.path.join(tmp_dir, "overwrite.txt")
        save_file(path, "old content")
        save_file(path, "new content")
        assert load_file(path) == "new content"

    def test_preserves_existing_file_permissions(self, tmp_dir):
        """Overwriting a file preserves its original permissions."""
        path = os.path.join(tmp_dir, "perms.txt")
        save_file(path, "initial")
        os.chmod(path, 0o644)
        save_file(path, "updated")
        mode = os.stat(path).st_mode & 0o777
        assert mode == 0o644, f"Expected 0o644, got {oct(mode)}"

    def test_new_file_default_permissions(self, tmp_dir):
        """New file gets default mkstemp permissions (0o600)."""
        path = os.path.join(tmp_dir, "new.txt")
        save_file(path, "content")
        mode = os.stat(path).st_mode & 0o777
        assert mode == 0o600, f"Expected 0o600, got {oct(mode)}"

    def test_rejects_non_string_content(self, tmp_dir):
        """Non-string content raises TypeError."""
        path = os.path.join(tmp_dir, "bad.txt")
        with pytest.raises(TypeError):
            save_file(path, 12345)

    def test_exactly_64kb_with_multibyte(self, tmp_dir):
        """File at exactly 64KB byte size with multibyte chars saves OK."""
        # 64 * 1024 = 65536 bytes; each emoji is 4 bytes
        num_chars = (64 * 1024) // 4  # = 16384 chars = exactly 65536 bytes
        content = "\U0001f600" * num_chars
        assert len(content.encode("utf-8")) == 64 * 1024

        path = os.path.join(tmp_dir, "exact_64kb.txt")
        save_file(path, content)
        assert load_file(path) == content
