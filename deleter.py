"""
deleter.py — Interactive duplicate deletion for dupefind
"""

import os
from pathlib import Path
from typing import List, Optional


def _human_size(size: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"


class Deleter:
    def __init__(
        self,
        groups: List[List[Path]],
        keep: Optional[str] = None,
        dry_run: bool = False,
    ):
        self.groups = groups
        self.keep = keep
        self.dry_run = dry_run
        self.deleted = 0
        self.reclaimed = 0

    def run(self):
        if self.dry_run:
            print("  ⚠️  DRY RUN — no files will actually be deleted\n")

        for i, group in enumerate(self.groups, 1):
            print(f"\n  ── Group {i} of {len(self.groups)} ──")
            for j, f in enumerate(group):
                try:
                    size = f.stat().st_size
                    label = _human_size(size)
                except OSError:
                    label = "?"
                print(f"    [{j}] {f}  ({label})")

            if self.keep:
                to_delete = self._auto_select(group)
                for f in to_delete:
                    self._delete(f)
            else:
                self._interactive(group)

        print(f"\n  ✅  Done. Deleted {self.deleted} file(s), "
              f"reclaimed {_human_size(self.reclaimed)}.\n")

    def _auto_select(self, group: List[Path]) -> List[Path]:
        """Pick which file to keep based on --keep strategy."""
        try:
            if self.keep == "newest":
                keeper = max(group, key=lambda f: f.stat().st_mtime)
            elif self.keep == "oldest":
                keeper = min(group, key=lambda f: f.stat().st_mtime)
            elif self.keep == "largest":
                keeper = max(group, key=lambda f: f.stat().st_size)
            elif self.keep == "smallest":
                keeper = min(group, key=lambda f: f.stat().st_size)
            else:
                keeper = group[0]
        except OSError:
            keeper = group[0]

        print(f"    → Keeping ({self.keep}): {keeper}")
        return [f for f in group if f != keeper]

    def _interactive(self, group: List[Path]):
        print(f"\n    Enter index to KEEP (others deleted), or 's' to skip: ", end="")
        try:
            choice = input().strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n  Aborted.")
            return

        if choice == "s":
            print("    Skipped.")
            return

        try:
            keep_idx = int(choice)
            if keep_idx < 0 or keep_idx >= len(group):
                raise ValueError
        except ValueError:
            print(f"    Invalid choice, skipping group.")
            return

        keeper = group[keep_idx]
        for j, f in enumerate(group):
            if j != keep_idx:
                self._delete(f)

    def _delete(self, path: Path):
        try:
            size = path.stat().st_size
        except OSError:
            size = 0

        if self.dry_run:
            print(f"    [dry-run] Would delete: {path}")
        else:
            try:
                path.unlink()
                self.deleted += 1
                self.reclaimed += size
                print(f"    🗑️  Deleted: {path}")
            except OSError as e:
                print(f"    [error] Could not delete {path}: {e}")
