"""
tests/test_scanner.py — Unit tests for dupefind
"""

import hashlib
import os
import tempfile
from pathlib import Path

import pytest

from dupefind.scanner import DuplicateScanner


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


def write(path: Path, content: bytes):
    path.write_bytes(content)
    return path


class TestDuplicateScanner:

    def test_no_duplicates(self, temp_dir):
        write(temp_dir / "a.txt", b"hello")
        write(temp_dir / "b.txt", b"world")
        scanner = DuplicateScanner([temp_dir])
        groups = scanner.scan()
        assert groups == []

    def test_finds_exact_duplicates(self, temp_dir):
        content = b"duplicate content"
        write(temp_dir / "file1.txt", content)
        write(temp_dir / "file2.txt", content)
        write(temp_dir / "file3.txt", content)
        scanner = DuplicateScanner([temp_dir])
        groups = scanner.scan()
        assert len(groups) == 1
        assert len(groups[0]) == 3

    def test_same_size_different_content(self, temp_dir):
        write(temp_dir / "a.txt", b"AAAA")
        write(temp_dir / "b.txt", b"BBBB")
        scanner = DuplicateScanner([temp_dir])
        groups = scanner.scan()
        assert groups == []

    def test_min_size_filter(self, temp_dir):
        write(temp_dir / "small1.txt", b"hi")
        write(temp_dir / "small2.txt", b"hi")
        write(temp_dir / "big1.txt", b"x" * 1024)
        write(temp_dir / "big2.txt", b"x" * 1024)
        # Only files >= 100 bytes
        scanner = DuplicateScanner([temp_dir], min_size=100)
        groups = scanner.scan()
        assert len(groups) == 1
        assert all(f.name.startswith("big") for f in groups[0])

    def test_recursive_true(self, temp_dir):
        sub = temp_dir / "subdir"
        sub.mkdir()
        content = b"same content"
        write(temp_dir / "file1.txt", content)
        write(sub / "file2.txt", content)
        scanner = DuplicateScanner([temp_dir], recursive=True)
        groups = scanner.scan()
        assert len(groups) == 1

    def test_recursive_false(self, temp_dir):
        sub = temp_dir / "subdir"
        sub.mkdir()
        content = b"same content"
        write(temp_dir / "file1.txt", content)
        write(sub / "file2.txt", content)
        scanner = DuplicateScanner([temp_dir], recursive=False)
        groups = scanner.scan()
        # file2.txt is in a subdirectory, should not be found
        assert groups == []

    def test_multiple_paths(self, temp_dir):
        dir_a = temp_dir / "a"
        dir_b = temp_dir / "b"
        dir_a.mkdir()
        dir_b.mkdir()
        content = b"shared file"
        write(dir_a / "file.txt", content)
        write(dir_b / "file.txt", content)
        scanner = DuplicateScanner([dir_a, dir_b])
        groups = scanner.scan()
        assert len(groups) == 1

    def test_hash_algorithms(self, temp_dir):
        content = b"test content"
        write(temp_dir / "f1.txt", content)
        write(temp_dir / "f2.txt", content)
        for algo in ("md5", "sha1", "sha256"):
            scanner = DuplicateScanner([temp_dir], hash_algo=algo)
            groups = scanner.scan()
            assert len(groups) == 1, f"Failed with algo={algo}"

    def test_empty_directory(self, temp_dir):
        scanner = DuplicateScanner([temp_dir])
        groups = scanner.scan()
        assert groups == []

    def test_single_file(self, temp_dir):
        write(temp_dir / "only.txt", b"only me")
        scanner = DuplicateScanner([temp_dir])
        groups = scanner.scan()
        assert groups == []
