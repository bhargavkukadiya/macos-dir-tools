# 🧰 macOS Dir Tools

A collection of macOS-friendly CLI tools for directory comparison, folder scanning, disk usage analysis, and duplicate file detection.

| | |
|---|---|
| **Author** | [Bhargav Kukadiya](https://github.com/bhargavkukadiya) |
| **Platform** | macOS & Linux |
| **Languages** | Bash, Python 3 |
| **License** | [MIT](LICENSE) |

## 📂 Directory Structure

```
macos-dir-tools/
├── .gitignore        # Git ignore rules
├── compare_dirs.sh   # Directory content comparison (4 methods)
├── dir_stats.sh      # Directory disk usage statistics
├── find_dupes.py     # Duplicate file finder
├── scan_folder.py    # Directory listing (JSON, CSV, Tree, List)
├── LICENSE           # MIT License
└── README.md
```

---

## 🔍 Compare Dirs (`compare_dirs.sh`)

Compares the contents of two directories using four distinct methods, with special handling for macOS-specific files like `.DS_Store` and `._*` (AppleDouble). Automatically detects and uses `md5` on macOS and `md5sum` on Linux.

### Usage

```bash
chmod +x compare_dirs.sh
./compare_dirs.sh <dir1> <dir2> [options]
```

### Options

| Option | Description |
|---|---|
| `-m`, `--method <1\|2\|3\|4>` | Run only the specified method (default: all) |
| `-q`, `--quiet` | Only show differences, suppress headers when clean |
| `--no-color` | Disable colored output |

### Methods

| Method | Description |
|--------|-------------|
| **1** | Compare full MD5 checksums with relative file paths |
| **2** | Compare only content hashes, ignoring file paths |
| **3** | Like Method 2, but also excludes AppleDouble (`._*`) files |
| **4** | Recursive `diff -rq`, suppressing AppleDouble file differences |

---

## 📁 Scan Folder (`scan_folder.py`)

Lists files and folders in a specified directory and outputs results in JSON, CSV, plain-text list, or a visual tree format.

### Features
- Includes file metadata (size, permissions, modified date)
- Tree format visualization
- Glob exclusion support (e.g., `node_modules`, `*.pyc`)
- Limits by recursion depth
- Optional summary stats

### Usage

```bash
# Basic usage
python scan_folder.py /path/to/folder

# Visual tree view with hidden files
python scan_folder.py /path/to/folder --format tree --hidden

# JSON output, recursive, excluding certain folders
python scan_folder.py /path/to/folder -r --exclude "node_modules" "*.git" --format json

# Export to CSV for spreadsheet workflows
python scan_folder.py /path/to/folder -r --format csv > inventory.csv
```

### Arguments

| Argument | Description |
|---|---|
| `-r`, `-R`, `--recursive` | List subdirectories recursively |
| `-a`, `-H`, `--hidden` | Include hidden files and folders |
| `-f`, `-F`, `--files-only` | Only list files, omit folders |
| `--format {json,list,tree,csv}` | Output format (default: `json`) |
| `--exclude PATTERN [PATTERN ...]` | Glob patterns to exclude |
| `--depth N` | Maximum recursion depth |
| `--summary` | Print a summary line (counts, total size) |

---

## 📊 Directory Stats (`dir_stats.sh`)

Displays disk usage statistics for a directory, broken down by file type extension. Automatically excludes macOS metadata files (`.DS_Store`, `._*`).

### Usage

```bash
chmod +x dir_stats.sh
./dir_stats.sh /path/to/folder [options]
```

### Options

| Option | Description |
|---|---|
| `-n`, `--top <N>` | Show top N file types by size (default: 10) |
| `-a`, `--all` | Include hidden files and directories |
| `--no-color` | Disable colored output |

---

## 👯 Find Duplicates (`find_dupes.py`)

Finds duplicate files by content hash (MD5). Groups duplicates together and reports wasted space, helping you clean up your drives.

### Usage

```bash
# Find dupes over 1MB
python find_dupes.py /path/to/folder -r --min-size 1MB

# Ignore specific file types
python find_dupes.py /path/to/folder -r --exclude "*.log" "*.tmp"
```

### Arguments

| Argument | Description |
|---|---|
| `-r`, `-R`, `--recursive` | Scan subdirectories recursively |
| `-a`, `--hidden` | Include hidden files |
| `--min-size SIZE` | Minimum file size (e.g., `1KB`, `5MB`). Default: 0 |
| `--max-size SIZE` | Maximum file size (e.g., `1GB`) |
| `--exclude PATTERN [PATTERN ...]` | Glob patterns to exclude |
| `--format {text,json}` | Output format (default: `text`) |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -m 'Add my feature'`)
4. Push to the branch (`git push origin feature/my-feature`)
5. Open a Pull Request

---

## 📃 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

Copyright © 2026 [Bhargav Kukadiya](https://github.com/bhargavkukadiya)
