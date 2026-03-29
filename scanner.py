"""
scanner.py — Core duplicate detection engine for dupefind
"""

import hashlib
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List


class DuplicateScanner:
    def __init__(
        self,
        paths: List[Path],
        min_size: int = 1,
        hash_algo: str = "sha256",
        recursive: bool = True,
    ):
        self.paths = paths
        self.min_size = min_size
        self.hash_algo = hash_algo
        self.recursive = recursive

    def _iter_files(self) -> List[Path]:
        """Walk directories and yield all files meeting the size threshold."""
        found = []
        for root_path in self.paths:
            if self.recursive:
                walker = root_path.rglob("*")
            else:
                walker = root_path.glob("*")
            for f in walker:
                try:
                    if f.is_file() and not f.is_symlink():
                        if f.stat().st_size >= self.min_size:
                            found.append(f)
                except (PermissionError, OSError):
                    print(f"  [skip] Permission denied: {f}", file=sys.stderr)
        return found

    def _hash_file(self, path: Path, chunk_size: int = 65536) -> str:
        """Compute the hash of a file."""
        h = hashlib.new(self.hash_algo)
        try:
            with open(path, "rb") as f:
                while chunk := f.read(chunk_size):
                    h.update(chunk)
        except (PermissionError, OSError) as e:
            print(f"  [skip] Cannot read {path}: {e}", file=sys.stderr)
            return ""
        return h.hexdigest()

    def scan(self) -> List[List[Path]]:
        """
        Full scan pipeline:
          1. Collect all files
          2. Group by size (fast pre-filter)
          3. Hash files in same-size groups
          4. Return groups of duplicates (2+ files with same hash)
        """
        print("  Step 1/3  Collecting files...")
        all_files = self._iter_files()
        print(f"            Found {len(all_files)} file(s) ≥ {self.min_size} byte(s)\n")

        # Group by size
        by_size: Dict[int, List[Path]] = defaultdict(list)
        for f in all_files:
            try:
                by_size[f.stat().st_size].append(f)
            except OSError:
                pass

        candidates = [files for files in by_size.values() if len(files) > 1]
        candidate_count = sum(len(g) for g in candidates)

        print(f"  Step 2/3  Hashing {candidate_count} candidate file(s) "
              f"({len(candidates)} size group(s))...")

        by_hash: Dict[str, List[Path]] = defaultdict(list)
        hashed = 0
        for group in candidates:
            for f in group:
                digest = self._hash_file(f)
                if digest:
                    by_hash[digest].append(f)
                hashed += 1
                self._print_progress(hashed, candidate_count)

        print()  # newline after progress

        print("  Step 3/3  Grouping duplicates...\n")
        duplicates = [
            sorted(files, key=lambda p: p.stat().st_mtime)
            for files, _ in (
                (files, digest)
                for digest, files in by_hash.items()
                if len(files) > 1
            )
        ]

        # Re-filter using hash (not size) — already done above, clean up
        duplicates = [
            sorted(files, key=lambda p: p.stat().st_mtime)
            for digest, files in by_hash.items()
            if len(files) > 1
            for files in [by_hash[digest]]
        ]

        return duplicates

    @staticmethod
    def _print_progress(current: int, total: int):
        if total == 0:
            return
        pct = int((current / total) * 40)
        bar = "█" * pct + "░" * (40 - pct)
        print(f"\r  [{bar}] {current}/{total}", end="", flush=True)
