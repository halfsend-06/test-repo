"""Tests for file_saver module.

Verifies that save_file correctly handles UTF-8 multibyte characters
at various file sizes, especially around the 64KB buffer boundary.
"""

import os

from src.file_saver import save_file


def _read_file(path: str) -> str:
    """Read a UTF-8 file inline (reads directly to avoid depending on the module under test)."""
    with open(path, "rb") as fh:
        return fh.read().decode("utf-8")


def _make_multibyte_content(target_bytes: int) -> str:
    """Build a string of emoji characters whose UTF-8 encoding is
    approximately *target_bytes* bytes long.

    Each emoji (U+1F600 GRINNING FACE) is 4 bytes in UTF-8.
    """
    chars_needed = target_bytes // 4
    return "\U0001f600" * chars_needed


def _make_ascii_content(target_bytes: int) -> str:
    """Build an ASCII string of *target_bytes* bytes."""
    return "A" * target_bytes


def _make_cjk_content(target_bytes: int) -> str:
    """Build a string of CJK characters whose UTF-8 encoding is
    approximately *target_bytes* bytes long.

    Each CJK character (U+4E00 CJK UNIFIED IDEOGRAPH) is 3 bytes in UTF-8.
    """
    chars_needed = target_bytes // 3
    return "一" * chars_needed


def _make_mixed_content(target_bytes: int) -> str:
    """Build a string mixing ASCII and multibyte characters whose
    UTF-8 encoding is approximately *target_bytes* bytes long.
    """
    # Alternate between ASCII ('A', 1 byte) and emoji (4 bytes).
    # Each pair is 5 bytes.
    pairs = target_bytes // 5
    remainder = target_bytes - pairs * 5
    return ("A\U0001f600" * pairs) + ("A" * remainder)


class TestSaveFile:
    """Test saving files with various content types and sizes."""

    def test_save_under_64kb_multibyte(self, tmp_path):
        """63KB file with multibyte UTF-8 chars should save and
        round-trip successfully."""
        content = _make_multibyte_content(63 * 1024)
        path = str(tmp_path / "under64kb.txt")
        save_file(path, content)
        assert _read_file(path) == content

    def test_save_exact_64kb_multibyte(self, tmp_path):
        """Exact 64KB (65536 bytes) file with multibyte UTF-8 chars
        should save and round-trip successfully (boundary case)."""
        content = _make_multibyte_content(65536)
        path = str(tmp_path / "exact64kb.txt")
        save_file(path, content)
        assert _read_file(path) == content

    def test_save_over_64kb_multibyte(self, tmp_path):
        """65KB file with multibyte UTF-8 chars should save and
        round-trip successfully (previously caused segfault)."""
        content = _make_multibyte_content(65 * 1024)
        path = str(tmp_path / "over64kb.txt")
        save_file(path, content)
        assert _read_file(path) == content

    def test_save_over_64kb_ascii(self, tmp_path):
        """65KB ASCII-only file should save and round-trip
        successfully (control case)."""
        content = _make_ascii_content(65 * 1024)
        path = str(tmp_path / "over64kb_ascii.txt")
        save_file(path, content)
        assert _read_file(path) == content

    def test_save_over_64kb_cjk(self, tmp_path):
        """65KB file with CJK characters (3-byte UTF-8 sequences)
        should save and round-trip successfully."""
        content = _make_cjk_content(65 * 1024)
        path = str(tmp_path / "over64kb_cjk.txt")
        save_file(path, content)
        assert _read_file(path) == content

    def test_save_128kb_mixed(self, tmp_path):
        """128KB mixed ASCII/multibyte file should save and
        round-trip successfully."""
        content = _make_mixed_content(128 * 1024)
        path = str(tmp_path / "mixed128kb.txt")
        save_file(path, content)
        assert _read_file(path) == content

    def test_byte_length_matches(self, tmp_path):
        """Written file byte length must equal the UTF-8 encoded
        length, not the Python character count."""
        content = _make_multibyte_content(70 * 1024)
        path = str(tmp_path / "bytecheck.txt")
        save_file(path, content)
        file_size = os.path.getsize(path)
        expected_size = len(content.encode("utf-8"))
        assert file_size == expected_size

    def test_empty_file(self, tmp_path):
        """Saving an empty string should produce an empty file."""
        path = str(tmp_path / "empty.txt")
        save_file(path, "")
        assert _read_file(path) == ""
        assert os.path.getsize(path) == 0
