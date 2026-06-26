# 🧰 macOS Dir Tools

A collection of macOS-friendly CLI tools for directory comparison and folder scanning.

| | |
|---|---|
| **Author** | [Bhargav Kukadiya](https://github.com/bhargavkukadiya) |
| **Platform** | macOS · Linux (partial) |
| **Languages** | Bash, Python 3 |
| **License** | [MIT](LICENSE) |

## 📂 Directory Structure

```
macos-dir-tools/
├── .gitignore        # Git ignore rules
├── compare_dirs.sh   # Directory content comparison (4 methods)
├── scan_folder.py    # Directory listing with JSON/list output
├── LICENSE           # MIT License
└── README.md
```

---

## Compare Dirs (`compare_dirs.sh`)

Compares the contents of two directories using four distinct methods, with special handling for macOS-specific files like `.DS_Store` and `._*` (AppleDouble).

### Usage

```bash
chmod +x compare_dirs.sh
./compare_dirs.sh <dir1> <dir2>
```

### Methods

| Method | Description |
|--------|-------------|
| **1** | Compare full MD5 checksums with relative file paths |
| **2** | Compare only content hashes, ignoring file paths |
| **3** | Like Method 2, but also excludes AppleDouble (`._*`) files |
| **4** | Recursive `diff -rq`, suppressing AppleDouble file differences |

### Notes

- Temporary files are created in a system temp directory and cleaned up automatically.
- This script uses the macOS `md5` command. For Linux, replace with `md5sum` and adjust field extraction.

---

## Scan Folder (`scan_folder.py`)

Lists files and folders in a specified directory and outputs results in JSON or plain-text format.

### Features

- List all files and folders in a specified directory
- Optionally include hidden files and folders
- Optionally list files and folders recursively
- Filter to files only
- Output in JSON or list format
- Results are sorted by path for deterministic output

### Requirements

- Python 3.x

### Usage

```bash
python scan_folder.py /path/to/folder
```

#### Include Hidden Files

```bash
python scan_folder.py /path/to/folder --hidden
```

#### List Recursively

```bash
python scan_folder.py /path/to/folder --recursive
```

#### Files Only

```bash
python scan_folder.py /path/to/folder --files-only
```

#### Output as List

```bash
python scan_folder.py /path/to/folder --format list
```

#### Combine Options

```bash
python scan_folder.py /path/to/folder --hidden --recursive --files-only --format json
```

### Arguments

| Argument | Description |
|---|---|
| `-r`, `-R`, `--recursive` | List subdirectories recursively |
| `-a`, `-H`, `--hidden` | Include hidden files and folders |
| `-f`, `-F`, `--files-only` | Only list files, omit folders |
| `--format {json,list}` | Output format (default: `json`) |

### Output Example (JSON)

```json
[
  {
    "name": "file1.txt",
    "path": "/path/to/folder/file1.txt",
    "type": "file"
  },
  {
    "name": "subfolder",
    "path": "/path/to/folder/subfolder",
    "type": "folder"
  }
]
```

### Output Example (List)

```
[F] /path/to/folder/file1.txt
[D] /path/to/folder/subfolder
```

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
