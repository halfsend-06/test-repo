"""Tests for file_saver module.

Verifies that save_file correctly handles UTF-8 multibyte characters
at various file sizes, especially around the 64KB buffer boundary.
"""

import os

from src.file_saver import _BUFFER_SIZE, save_file


def _read_file(path: str) -> str:
    """Read a UTF-8 file back for verification."""
    with open(path, "rb") as fh:
        return fh.read().decode("utf-8")


def _make_multibyte_content(target_bytes: int) -> str:
    """Build a string of emoji whose UTF-8 encoding is approximately
    *target_bytes* bytes long.  Each emoji (U+1F600) is 4 bytes."""
    return "\U0001f600" * (target_bytes // 4)


def _make_ascii_content(target_bytes: int) -> str:
    """Build an ASCII string of *target_bytes* bytes."""
    return "A" * target_bytes


def _make_cjk_content(target_bytes: int) -> str:
    """Build CJK characters (~*target_bytes* bytes).
    Each CJK char (U+4E00) is 3 bytes in UTF-8."""
    return "一" * (target_bytes // 3)


class TestSaveFile:
    """Boundary and encoding tests for save_file."""

    def test_ascii_over_64kb(self, tmp_path):
        """ASCII-only file >64KB saves successfully (control case)."""
        content = _make_ascii_content(65 * 1024)
        dest = str(tmp_path / "ascii_65k.txt")
        save_file(dest, content)
        assert _read_file(dest) == content

    def test_multibyte_under_64kb(self, tmp_path):
        """Multibyte file <64KB saves successfully."""
        content = _make_multibyte_content(63 * 1024)
        dest = str(tmp_path / "mb_under.txt")
        save_file(dest, content)
        assert _read_file(dest) == content

    def test_multibyte_at_boundary(self, tmp_path):
        """Multibyte file at exactly 64KB boundary saves."""
        content = _make_multibyte_content(_BUFFER_SIZE)
        dest = str(tmp_path / "mb_boundary.txt")
        save_file(dest, content)
        assert _read_file(dest) == content

    def test_multibyte_over_64kb(self, tmp_path):
        """Multibyte file >64KB saves successfully.
        This is the scenario that caused the v2.3.1 segfault."""
        content = _make_multibyte_content(70 * 1024)
        dest = str(tmp_path / "mb_over.txt")
        save_file(dest, content)
        assert _read_file(dest) == content

    def test_cjk_over_64kb(self, tmp_path):
        """CJK file >64KB (3-byte sequences) saves successfully."""
        content = _make_cjk_content(70 * 1024)
        dest = str(tmp_path / "cjk_over.txt")
        save_file(dest, content)
        assert _read_file(dest) == content

    def test_byte_length_preserved(self, tmp_path):
        """On-disk byte length equals UTF-8 encoded length,
        not the Python character count."""
        content = _make_multibyte_content(70 * 1024)
        dest = str(tmp_path / "bytecheck.txt")
        save_file(dest, content)
        assert os.path.getsize(dest) == len(content.encode("utf-8"))

    def test_empty_file(self, tmp_path):
        """Saving an empty string produces an empty file."""
        dest = str(tmp_path / "empty.txt")
        save_file(dest, "")
        assert _read_file(dest) == ""
        assert os.path.getsize(dest) == 0
