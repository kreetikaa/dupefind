"""
reporter.py — Output formatting for dupefind results
"""

import json
import csv
import sys
import os
from pathlib import Path
from typing import List


def _human_size(size: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"


class Reporter:
    def __init__(self, output_format: str = "table"):
        self.format = output_format

    def report(self, groups: List[List[Path]]):
        if self.format == "table":
            self._table(groups)
        elif self.format == "json":
            self._json(groups)
        elif self.format == "csv":
            self._csv(groups)

    def _table(self, groups: List[List[Path]]):
        total_wasted = 0
        print(f"{'─' * 70}")
        print(f"  Found {len(groups)} duplicate group(s)\n")

        for i, group in enumerate(groups, 1):
            try:
                size = group[0].stat().st_size
            except OSError:
                size = 0
            wasted = size * (len(group) - 1)
            total_wasted += wasted

            print(f"  Group {i}  ·  {len(group)} files  ·  {_human_size(size)} each"
                  f"  ·  {_human_size(wasted)} wasted")
            print(f"  {'─' * 66}")
            for f in group:
                try:
                    mtime = f.stat().st_mtime
                    import datetime
                    dt = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
                except OSError:
                    dt = "unknown"
                print(f"    {dt}  {f}")
            print()

        print(f"{'─' * 70}")
        print(f"  💾  Total reclaimable space: {_human_size(total_wasted)}")
        print(f"{'─' * 70}\n")

    def _json(self, groups: List[List[Path]]):
        output = []
        for i, group in enumerate(groups, 1):
            try:
                size = group[0].stat().st_size
            except OSError:
                size = 0
            output.append({
                "group": i,
                "file_size_bytes": size,
                "file_size_human": _human_size(size),
                "count": len(group),
                "wasted_bytes": size * (len(group) - 1),
                "files": [str(f) for f in group],
            })
        print(json.dumps(output, indent=2))

    def _csv(self, groups: List[List[Path]]):
        writer = csv.writer(sys.stdout)
        writer.writerow(["group", "file", "size_bytes", "size_human"])
        for i, group in enumerate(groups, 1):
            try:
                size = group[0].stat().st_size
            except OSError:
                size = 0
            for f in group:
                writer.writerow([i, str(f), size, _human_size(size)])
