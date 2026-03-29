"""
dupefind - A fast duplicate file finder for Linux
"""

import argparse
import sys
from pathlib import Path

from .scanner import DuplicateScanner
from .reporter import Reporter


def parse_args():
    parser = argparse.ArgumentParser(
        prog="dupefind",
        description="🔍 dupefind — Find and manage duplicate files on your system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  dupefind /home/user/Documents
  dupefind /home/user --min-size 1MB --delete
  dupefind /var/backups --output json
  dupefind . --hash md5 --recursive
        """,
    )

    parser.add_argument(
        "path",
        nargs="+",
        type=Path,
        help="One or more directories to scan",
    )

    parser.add_argument(
        "--min-size",
        default="1",
        metavar="SIZE",
        help="Minimum file size to consider (e.g. 1, 100KB, 10MB). Default: 1 byte",
    )

    parser.add_argument(
        "--hash",
        choices=["md5", "sha1", "sha256"],
        default="sha256",
        help="Hashing algorithm to use (default: sha256)",
    )

    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="Do not recurse into subdirectories",
    )

    parser.add_argument(
        "--output",
        choices=["table", "json", "csv"],
        default="table",
        help="Output format (default: table)",
    )

    parser.add_argument(
        "--delete",
        action="store_true",
        help="Interactively choose duplicates to delete",
    )

    parser.add_argument(
        "--keep",
        choices=["newest", "oldest", "largest", "smallest"],
        help="When used with --delete, auto-keep this file from each group",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting",
    )

    parser.add_argument(
        "--version",
        action="version",
        version="dupefind 1.0.0",
    )

    return parser.parse_args()


def parse_size(size_str: str) -> int:
    """Convert human-readable size string to bytes."""
    size_str = size_str.strip().upper()
    units = {"B": 1, "KB": 1024, "MB": 1024**2, "GB": 1024**3, "TB": 1024**4}
    for suffix, multiplier in sorted(units.items(), key=lambda x: -len(x[0])):
        if size_str.endswith(suffix):
            try:
                return int(float(size_str[: -len(suffix)]) * multiplier)
            except ValueError:
                pass
    try:
        return int(size_str)
    except ValueError:
        print(f"[error] Invalid size format: '{size_str}'. Use e.g. 100KB, 10MB.")
        sys.exit(1)


def main():
    args = parse_args()
    min_size = parse_size(args.min_size)

    # Validate paths
    for p in args.path:
        if not p.exists():
            print(f"[error] Path does not exist: {p}")
            sys.exit(1)
        if not p.is_dir():
            print(f"[error] Not a directory: {p}")
            sys.exit(1)

    scanner = DuplicateScanner(
        paths=args.path,
        min_size=min_size,
        hash_algo=args.hash,
        recursive=not args.no_recursive,
    )

    reporter = Reporter(output_format=args.output)

    print(f"\n🔍 dupefind — scanning {len(args.path)} path(s)...\n")
    groups = scanner.scan()

    if not groups:
        print("✅  No duplicates found.")
        return

    reporter.report(groups)

    if args.delete:
        from .deleter import Deleter
        deleter = Deleter(groups, keep=args.keep, dry_run=args.dry_run)
        deleter.run()


if __name__ == "__main__":
    main()
