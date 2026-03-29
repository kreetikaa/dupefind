# 🔍 dupefind

A fast, zero-dependency duplicate file finder for Linux — built with pure Python.

```
$ dupefind ~/Downloads ~/Documents

🔍 dupefind — scanning 2 path(s)...

  Step 1/3  Collecting files...
            Found 1,203 file(s) ≥ 1 byte(s)

  Step 2/3  Hashing 417 candidate file(s) (128 size group(s))...
  [████████████████████████████████████████] 417/417

  Step 3/3  Grouping duplicates...

──────────────────────────────────────────────────────────────────────
  Found 3 duplicate group(s)

  Group 1  ·  2 files  ·  4.2 MB each  ·  4.2 MB wasted
  ────────────────────────────────────────────────────────────────────
    2024-01-15 10:22  /home/user/Downloads/report.pdf
    2024-03-02 18:41  /home/user/Documents/report.pdf

  ...

──────────────────────────────────────────────────────────────────────
  💾  Total reclaimable space: 9.7 MB
──────────────────────────────────────────────────────────────────────
```

## Features

- ⚡ **Two-pass detection** — groups by size first, hashes only candidates (fast)
- 🔐 **Multiple algorithms** — MD5, SHA-1, SHA-256
- 🗂️ **Multiple output formats** — human table, JSON, CSV
- 🗑️ **Safe deletion** — interactive mode or auto-keep strategy + dry-run
- 📦 **Zero dependencies** — pure Python stdlib, works everywhere
- 🐧 **Linux-first** — skips symlinks, handles permission errors gracefully

---

## Installation

### From PyPI (recommended)

```bash
pip install dupefind
```

### From source

```bash
git clone https://github.com/yourname/dupefind.git
cd dupefind
pip install -e .
```

---

## Usage

```
dupefind [OPTIONS] PATH [PATH ...]
```

### Arguments

| Argument | Description |
|----------|-------------|
| `PATH`   | One or more directories to scan (can specify multiple) |

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--min-size SIZE` | `1` | Minimum file size to consider. Supports `B`, `KB`, `MB`, `GB` (e.g. `10MB`) |
| `--hash {md5,sha1,sha256}` | `sha256` | Hashing algorithm |
| `--no-recursive` | — | Don't recurse into subdirectories |
| `--output {table,json,csv}` | `table` | Output format |
| `--delete` | — | Interactively select which duplicates to delete |
| `--keep {newest,oldest,largest,smallest}` | — | Auto-keep strategy when used with `--delete` |
| `--dry-run` | — | Show what would be deleted without deleting |
| `--version` | — | Show version and exit |

### Examples

```bash
# Scan a single directory
dupefind ~/Downloads

# Scan multiple directories
dupefind ~/Downloads ~/Documents ~/Desktop

# Only consider files larger than 10 MB
dupefind /var/log --min-size 10MB

# Output as JSON (pipe-friendly)
dupefind ~/Pictures --output json | jq '.[] | .files'

# Output as CSV
dupefind ~/Music --output csv > dupes.csv

# Use faster (less secure) MD5 hashing
dupefind ~/Videos --hash md5

# Interactively delete duplicates
dupefind ~/Downloads --delete

# Auto-delete keeping the newest file, with dry-run first
dupefind ~/Backups --delete --keep newest --dry-run
dupefind ~/Backups --delete --keep newest
```

---

## How It Works

dupefind uses a two-pass strategy to stay fast even on large directories:

```
All files
    │
    ▼ Filter by --min-size
    │
    ▼ Group by file size  ← fast, no I/O
    │   (discard unique sizes)
    │
    ▼ Hash each candidate ← reads file content
    │
    ▼ Group by hash
    │
    ▼ Report groups of 2+
```

This means if you have 10,000 files but only 200 share a size with another file, only those 200 get hashed — saving significant time on large datasets.

---

## Output Formats

### Table (default)
Human-readable summary with group info and reclaimable space.

### JSON
Machine-readable, suitable for scripting:
```json
[
  {
    "group": 1,
    "file_size_bytes": 4404224,
    "file_size_human": "4.2 MB",
    "count": 2,
    "wasted_bytes": 4404224,
    "files": [
      "/home/user/Downloads/report.pdf",
      "/home/user/Documents/report.pdf"
    ]
  }
]
```

### CSV
Flat format with one row per file — easy to import into spreadsheets.

---

## Project Structure

```
dupefind/
├── dupefind/
│   ├── __init__.py     # Package metadata
│   ├── cli.py          # Argument parsing & entry point
│   ├── scanner.py      # Core duplicate detection engine
│   ├── reporter.py     # Output formatting (table / JSON / CSV)
│   └── deleter.py      # Interactive & auto deletion
├── tests/
│   └── test_scanner.py
├── pyproject.toml      # Build & packaging config
├── LICENSE
└── README.md
```

---

## Running Tests

```bash
pip install pytest
pytest tests/
```

---

## Contributing

Contributions are welcome! Here's how to get started:

1. Fork the repo on GitHub
2. Clone your fork: `git clone https://github.com/yourname/dupefind.git`
3. Create a branch: `git checkout -b feature/my-feature`
4. Make your changes and add tests
5. Run the test suite: `pytest tests/`
6. Push and open a Pull Request

### Ideas for contributions
- [ ] Progress bar using `rich`
- [ ] Export to HTML report
- [ ] Watch mode (re-scan on changes)
- [ ] macOS / Windows support
- [ ] Config file (`~/.dupefind.toml`)
- [ ] Parallel hashing with `concurrent.futures`

---

## License

MIT © Your Name — see [LICENSE](LICENSE) for details.
