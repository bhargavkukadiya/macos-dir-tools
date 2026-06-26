"""
scan_folder.py — List files and folders in a directory.

Outputs a JSON or plain-text listing of files and directories for a given
path, with options for recursive traversal, hidden file inclusion, and
file-only filtering.

Usage:
    python scan_folder.py /path/to/folder
    python scan_folder.py /path/to/folder --recursive --hidden --format list
"""

import os
import sys
import json
import argparse


def list_directory(path, include_hidden=False, recursive=False, files_only=False):
    """
    Lists files and/or folders in a given path.

    Args:
        path (str): The path to the directory to list.
        include_hidden (bool): If True, includes hidden files and folders.
        recursive (bool): If True, lists contents of subdirectories recursively.
        files_only (bool): If True, only lists files and omits folders.

    Returns:
        list: A sorted list of dictionaries, each representing a file or folder.
    """
    result = []
    _explore(path, result, include_hidden, recursive, files_only)
    result.sort(key=lambda x: x['path'])
    return result


def _explore(current_path, result, include_hidden, recursive, files_only):
    """Recursively explores a directory and appends items to the result list."""
    try:
        for entry in os.scandir(current_path):
            if not include_hidden and entry.name.startswith('.'):
                continue

            # Use follow_symlinks=False to prevent infinite recursion on circular symlinks
            is_dir = entry.is_dir(follow_symlinks=False)

            if is_dir:
                if not files_only:
                    result.append({
                        'name': entry.name,
                        'path': entry.path,
                        'type': 'folder'
                    })
                if recursive:
                    _explore(entry.path, result, include_hidden, recursive, files_only)
            else:
                result.append({
                    'name': entry.name,
                    'path': entry.path,
                    'type': 'file'
                })
    except OSError as e:
        print(json.dumps({"error": f"Cannot access '{current_path}': {e}"}), file=sys.stderr)


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
        "--format", choices=["json", "list"], default="json",
        help="Output format (default: json)."
    )
    args = parser.parse_args()

    # Check if the provided path is a valid directory
    if not os.path.isdir(args.folder):
        print(
            json.dumps({"error": "The provided path is not a directory or does not exist."}),
            file=sys.stderr
        )
        sys.exit(1)

    # Get the directory listing based on the provided arguments
    data = list_directory(
        args.folder,
        include_hidden=args.hidden,
        recursive=args.recursive,
        files_only=args.files_only
    )

    if not data:
        print("No items found matching the criteria.")
        return

    if args.format == "json":
        print(json.dumps(data, indent=2))
    else:
        for item in data:
            prefix = "[D]" if item['type'] == 'folder' else "[F]"
            print(f"{prefix} {item['path']}")


if __name__ == "__main__":
    main()
