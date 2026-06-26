"""
find_dupes.py — Find duplicate files by content hash.

Scans a directory for files with identical content using MD5 hashes.
Groups duplicates together and reports wasted space.

Usage:
    python find_dupes.py /path/to/folder
    python find_dupes.py /path/to/folder --recursive --min-size 1MB --format json
"""

import os
import sys
import json
import hashlib
import argparse
from collections import defaultdict
from datetime import datetime


def _parse_size(size_str):
    """Parses a human-readable size string (e.g., '1MB', '500KB') into bytes."""
    size_str = size_str.strip().upper()
    units = {'B': 1, 'KB': 1024, 'MB': 1024**2, 'GB': 1024**3, 'TB': 1024**4}

    for unit, multiplier in sorted(units.items(), key=lambda x: -len(x[0])):
        if size_str.endswith(unit):
            try:
                return int(float(size_str[:-len(unit)]) * multiplier)
            except ValueError:
                print(f"Error: Invalid size format '{size_str}'", file=sys.stderr)
                sys.exit(1)

    # No unit suffix — treat as bytes
    try:
        return int(size_str)
    except ValueError:
        print(f"Error: Invalid size format '{size_str}'", file=sys.stderr)
        sys.exit(1)


def _format_size(size_bytes):
    """Formats a byte count into a human-readable string."""
    for unit in ('B', 'KB', 'MB', 'GB', 'TB'):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}" if unit != 'B' else f"{size_bytes} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


def _hash_file(filepath, chunk_size=8192):
    """Computes the MD5 hash of a file."""
    hasher = hashlib.md5()
    try:
        with open(filepath, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                hasher.update(chunk)
        return hasher.hexdigest()
    except OSError:
        return None


def find_duplicates(path, recursive=False, include_hidden=False,
                    min_size=0, max_size=None, exclude_patterns=None):
    """
    Finds duplicate files in a directory by content hash.

    Args:
        path (str): The directory to scan.
        recursive (bool): If True, scans subdirectories recursively.
        include_hidden (bool): If True, includes hidden files.
        min_size (int): Minimum file size in bytes to consider.
        max_size (int): Maximum file size in bytes to consider (None for no limit).
        exclude_patterns (list): File name patterns to exclude.

    Returns:
        list: A list of duplicate groups, each containing file details.
    """
    import fnmatch
    exclude_patterns = exclude_patterns or []

    # Phase 1: Group files by size (quick filter — different sizes can't be dupes)
    size_groups = defaultdict(list)
    _scan_files(path, size_groups, recursive, include_hidden, min_size, max_size,
                exclude_patterns)

    # Phase 2: For files with matching sizes, compute hashes
    hash_groups = defaultdict(list)
    for size, files in size_groups.items():
        if len(files) < 2:
            continue
        for filepath in files:
            file_hash = _hash_file(filepath)
            if file_hash:
                hash_groups[file_hash].append(filepath)

    # Phase 3: Build results for groups with 2+ files
    results = []
    for file_hash, files in hash_groups.items():
        if len(files) < 2:
            continue

        group_files = []
        for filepath in sorted(files):
            try:
                file_stat = os.stat(filepath)
                group_files.append({
                    'path': filepath,
                    'size': file_stat.st_size,
                    'size_human': _format_size(file_stat.st_size),
                    'modified': datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                })
            except OSError:
                continue

        if len(group_files) >= 2:
            wasted = group_files[0]['size'] * (len(group_files) - 1)
            results.append({
                'hash': file_hash,
                'count': len(group_files),
                'file_size': group_files[0]['size'],
                'file_size_human': group_files[0]['size_human'],
                'wasted_space': wasted,
                'wasted_space_human': _format_size(wasted),
                'files': group_files
            })

    # Sort by wasted space (largest first)
    results.sort(key=lambda x: x['wasted_space'], reverse=True)
    return results


def _scan_files(current_path, size_groups, recursive, include_hidden,
                min_size, max_size, exclude_patterns):
    """Scans a directory and groups files by size."""
    import fnmatch

    try:
        for entry in os.scandir(current_path):
            if not include_hidden and entry.name.startswith('.'):
                continue

            if any(fnmatch.fnmatch(entry.name, pat) for pat in exclude_patterns):
                continue

            is_dir = entry.is_dir(follow_symlinks=False)

            if is_dir:
                if recursive:
                    _scan_files(entry.path, size_groups, recursive, include_hidden,
                                min_size, max_size, exclude_patterns)
            else:
                try:
                    size = entry.stat(follow_symlinks=False).st_size
                    if size < min_size:
                        continue
                    if max_size is not None and size > max_size:
                        continue
                    size_groups[size].append(entry.path)
                except OSError:
                    continue
    except OSError as e:
        print(f"Warning: Cannot access '{current_path}': {e}", file=sys.stderr)


def main():
    """Parses command-line arguments and finds duplicate files."""
    parser = argparse.ArgumentParser(
        description="Find duplicate files by content hash."
    )
    parser.add_argument("folder", help="Path to the folder to scan.")
    parser.add_argument(
        "-r", "-R", "--recursive", action="store_true",
        help="Scan subdirectories recursively."
    )
    parser.add_argument(
        "-a", "--hidden", action="store_true",
        help="Include hidden files."
    )
    parser.add_argument(
        "--min-size", default="0", metavar="SIZE",
        help="Minimum file size to consider (e.g., '1KB', '5MB'). Default: 0."
    )
    parser.add_argument(
        "--max-size", default=None, metavar="SIZE",
        help="Maximum file size to consider (e.g., '100MB', '1GB')."
    )
    parser.add_argument(
        "--exclude", nargs="+", default=[], metavar="PATTERN",
        help="Glob patterns to exclude (e.g., '*.log' '.DS_Store')."
    )
    parser.add_argument(
        "--format", choices=["json", "text"], default="text",
        help="Output format (default: text)."
    )
    args = parser.parse_args()

    if not os.path.isdir(args.folder):
        print(
            json.dumps({"error": "The provided path is not a directory or does not exist."}),
            file=sys.stderr
        )
        sys.exit(1)

    min_size = _parse_size(args.min_size)
    max_size = _parse_size(args.max_size) if args.max_size else None

    # Always exclude .DS_Store by default
    exclude = list(args.exclude)
    if '.DS_Store' not in exclude:
        exclude.append('.DS_Store')

    print(f"Scanning '{args.folder}'...", file=sys.stderr)
    results = find_duplicates(
        args.folder,
        recursive=args.recursive,
        include_hidden=args.hidden,
        min_size=min_size,
        max_size=max_size,
        exclude_patterns=exclude
    )

    if not results:
        print("No duplicates found.")
        return

    if args.format == "json":
        print(json.dumps(results, indent=2))
    else:
        total_wasted = 0
        total_dupes = 0

        for group in results:
            total_wasted += group['wasted_space']
            total_dupes += group['count'] - 1

            print(f"\n--- {group['count']} copies ({group['file_size_human']} each) ---")
            for f in group['files']:
                print(f"  {f['path']}")
                print(f"    Modified: {f['modified']}")

        print(f"\n{'='*50}")
        print(f"Total: {len(results)} duplicate group(s), "
              f"{total_dupes} redundant file(s)")
        print(f"Wasted space: {_format_size(total_wasted)}")


if __name__ == "__main__":
    main()
