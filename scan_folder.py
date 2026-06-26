"""
scan_folder.py — List files and folders in a directory.

Outputs a JSON, plain-text, tree, or CSV listing of files and directories
for a given path, with options for recursive traversal, hidden file inclusion,
file-only filtering, glob exclusions, and depth limiting.

Usage:
    python scan_folder.py /path/to/folder
    python scan_folder.py /path/to/folder --recursive --hidden --format tree
    python scan_folder.py /path/to/folder -r --exclude "node_modules" "*.pyc" --format json
"""

import os
import sys
import csv
import json
import stat
import fnmatch
import argparse
from datetime import datetime
from io import StringIO


def _format_size(size_bytes):
    """Formats a byte count into a human-readable string."""
    for unit in ('B', 'KB', 'MB', 'GB', 'TB'):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}" if unit != 'B' else f"{size_bytes} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


def _format_permissions(mode):
    """Converts a file mode to a Unix-style permission string (e.g., rwxr-xr--)."""
    perms = ''
    for who in ('USR', 'GRP', 'OTH'):
        for what, letter in (('R', 'r'), ('W', 'w'), ('X', 'x')):
            if mode & getattr(stat, f'S_I{what}{who}'):
                perms += letter
            else:
                perms += '-'
    return perms


def list_directory(path, include_hidden=False, recursive=False, files_only=False,
                   exclude_patterns=None, max_depth=None):
    """
    Lists files and/or folders in a given path.

    Args:
        path (str): The path to the directory to list.
        include_hidden (bool): If True, includes hidden files and folders.
        recursive (bool): If True, lists contents of subdirectories recursively.
        files_only (bool): If True, only lists files and omits folders.
        exclude_patterns (list): Glob patterns to exclude (e.g., ["node_modules", "*.pyc"]).
        max_depth (int): Maximum recursion depth (None for unlimited).

    Returns:
        list: A sorted list of dictionaries, each representing a file or folder.
    """
    result = []
    exclude_patterns = exclude_patterns or []
    _explore(path, result, include_hidden, recursive, files_only, exclude_patterns, max_depth, 0)
    result.sort(key=lambda x: x['path'])
    return result


def _matches_exclude(name, exclude_patterns):
    """Checks if a name matches any of the exclusion glob patterns."""
    return any(fnmatch.fnmatch(name, pat) for pat in exclude_patterns)


def _explore(current_path, result, include_hidden, recursive, files_only,
             exclude_patterns, max_depth, current_depth):
    """Recursively explores a directory and appends items to the result list."""
    try:
        for entry in os.scandir(current_path):
            if not include_hidden and entry.name.startswith('.'):
                continue

            if _matches_exclude(entry.name, exclude_patterns):
                continue

            # Use follow_symlinks=False to prevent infinite recursion on circular symlinks
            is_dir = entry.is_dir(follow_symlinks=False)

            try:
                entry_stat = entry.stat(follow_symlinks=False)
                size = entry_stat.st_size if not is_dir else None
                modified = datetime.fromtimestamp(entry_stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                permissions = _format_permissions(entry_stat.st_mode)
            except OSError:
                size = None
                modified = None
                permissions = None

            if is_dir:
                if not files_only:
                    result.append({
                        'name': entry.name,
                        'path': entry.path,
                        'type': 'folder',
                        'modified': modified,
                        'permissions': permissions
                    })
                if recursive and (max_depth is None or current_depth < max_depth):
                    _explore(entry.path, result, include_hidden, recursive,
                             files_only, exclude_patterns, max_depth, current_depth + 1)
            else:
                result.append({
                    'name': entry.name,
                    'path': entry.path,
                    'type': 'file',
                    'size': size,
                    'size_human': _format_size(size) if size is not None else None,
                    'modified': modified,
                    'permissions': permissions
                })
    except OSError as e:
        print(json.dumps({"error": f"Cannot access '{current_path}': {e}"}), file=sys.stderr)


def _print_tree(base_path, include_hidden, files_only, exclude_patterns, max_depth):
    """Renders a tree-style directory listing."""
    print(os.path.basename(os.path.abspath(base_path)) + '/')
    _print_tree_recursive(base_path, '', include_hidden, files_only,
                          exclude_patterns, max_depth, 0)


def _print_tree_recursive(current_path, prefix, include_hidden, files_only,
                           exclude_patterns, max_depth, current_depth):
    """Recursively prints a directory tree."""
    try:
        entries = sorted(os.scandir(current_path), key=lambda e: e.name)
    except OSError as e:
        print(f"{prefix}[error: {e}]", file=sys.stderr)
        return

    # Filter entries
    filtered = []
    for entry in entries:
        if not include_hidden and entry.name.startswith('.'):
            continue
        if _matches_exclude(entry.name, exclude_patterns):
            continue
        is_dir = entry.is_dir(follow_symlinks=False)
        if files_only and is_dir:
            # Still need to recurse into dirs to find files, but don't show dirs
            if max_depth is None or current_depth < max_depth:
                _print_tree_recursive(entry.path, prefix, include_hidden, files_only,
                                       exclude_patterns, max_depth, current_depth + 1)
            continue
        filtered.append(entry)

    for i, entry in enumerate(filtered):
        is_last = (i == len(filtered) - 1)
        connector = '└── ' if is_last else '├── '
        is_dir = entry.is_dir(follow_symlinks=False)

        if is_dir:
            print(f"{prefix}{connector}{entry.name}/")
            extension = '    ' if is_last else '│   '
            if max_depth is None or current_depth < max_depth:
                _print_tree_recursive(entry.path, prefix + extension, include_hidden,
                                       files_only, exclude_patterns, max_depth, current_depth + 1)
        else:
            try:
                size = entry.stat(follow_symlinks=False).st_size
                size_str = f"  ({_format_size(size)})"
            except OSError:
                size_str = ""
            print(f"{prefix}{connector}{entry.name}{size_str}")


def _print_csv(data):
    """Outputs the listing in CSV format."""
    output = StringIO()
    fieldnames = ['name', 'path', 'type', 'size', 'size_human', 'modified', 'permissions']
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()
    for item in data:
        writer.writerow(item)
    print(output.getvalue(), end='')


def _print_summary(data):
    """Prints a summary line to stderr."""
    file_count = sum(1 for d in data if d['type'] == 'file')
    folder_count = sum(1 for d in data if d['type'] == 'folder')
    total_size = sum(d.get('size', 0) or 0 for d in data if d['type'] == 'file')

    parts = []
    if file_count:
        parts.append(f"{file_count} file{'s' if file_count != 1 else ''}")
    if folder_count:
        parts.append(f"{folder_count} folder{'s' if folder_count != 1 else ''}")
    parts.append(_format_size(total_size))

    print(f"\nSummary: {', '.join(parts)}", file=sys.stderr)


def main():
    """Parses command-line arguments and prints the directory listing."""
    parser = argparse.ArgumentParser(
        description="List files and folders in a directory."
    )
    parser.add_argument("folder", help="Path to the folder to be listed.")
    parser.add_argument(
        "-r", "-R", "--recursive", action="store_true",
        help="List subdirectories recursively."
    )
    parser.add_argument(
        "-a", "-H", "--hidden", action="store_true",
        help="Include hidden files and folders (those starting with a dot)."
    )
    parser.add_argument(
        "-f", "-F", "--files-only", action="store_true",
        help="Only list files, do not include folders in the output."
    )
    parser.add_argument(
        "--format", choices=["json", "list", "tree", "csv"], default="json",
        help="Output format (default: json)."
    )
    parser.add_argument(
        "--exclude", nargs="+", default=[], metavar="PATTERN",
        help="Glob patterns to exclude (e.g., 'node_modules' '*.pyc')."
    )
    parser.add_argument(
        "--depth", type=int, default=None, metavar="N",
        help="Maximum recursion depth (requires --recursive)."
    )
    parser.add_argument(
        "--summary", action="store_true",
        help="Print a summary line (file/folder counts, total size)."
    )
    args = parser.parse_args()

    # Check if the provided path is a valid directory
    if not os.path.isdir(args.folder):
        print(
            json.dumps({"error": "The provided path is not a directory or does not exist."}),
            file=sys.stderr
        )
        sys.exit(1)

    if args.depth is not None and not args.recursive:
        print("Warning: --depth has no effect without --recursive.", file=sys.stderr)

    # Tree format has its own rendering
    if args.format == "tree":
        _print_tree(
            args.folder,
            include_hidden=args.hidden,
            files_only=args.files_only,
            exclude_patterns=args.exclude,
            max_depth=args.depth if args.recursive else 0
        )
        if args.summary:
            data = list_directory(
                args.folder, include_hidden=args.hidden, recursive=args.recursive,
                files_only=args.files_only, exclude_patterns=args.exclude,
                max_depth=args.depth
            )
            _print_summary(data)
        return

    # Get the directory listing
    data = list_directory(
        args.folder,
        include_hidden=args.hidden,
        recursive=args.recursive,
        files_only=args.files_only,
        exclude_patterns=args.exclude,
        max_depth=args.depth
    )

    if not data:
        print("No items found matching the criteria.")
        return

    if args.format == "json":
        print(json.dumps(data, indent=2))
    elif args.format == "csv":
        _print_csv(data)
    else:
        for item in data:
            prefix = "[D]" if item['type'] == 'folder' else "[F]"
            size_str = f"  ({item.get('size_human', '')})" if item['type'] == 'file' else ""
            print(f"{prefix} {item['path']}{size_str}")

    if args.summary:
        _print_summary(data)


if __name__ == "__main__":
    main()
