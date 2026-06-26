#!/bin/bash
set -euo pipefail

# compare_dirs.sh
# --------------------------------------
# Compares the contents of two directories using four different methods,
# handling macOS metadata files like .DS_Store and AppleDouble files (._*).
#
# NOTE: This script uses the macOS `md5` command. For Linux, replace `md5`
# with `md5sum` and adjust the awk field extraction accordingly.
#
# Usage:
#   chmod +x compare_dirs.sh
#   ./compare_dirs.sh <dir1> <dir2>

# --- Input Validation ---
dir1="${1:?Usage: $0 <dir1> <dir2>}"
dir2="${2:?Usage: $0 <dir1> <dir2>}"

[[ -d "$dir1" ]] || { echo "Error: '$dir1' is not a directory" >&2; exit 1; }
[[ -d "$dir2" ]] || { echo "Error: '$dir2' is not a directory" >&2; exit 1; }

# Normalize to absolute paths so sed substitution works regardless of how paths are passed
dir1=$(cd "$dir1" && pwd)
dir2=$(cd "$dir2" && pwd)

# --- Temp Directory with Cleanup ---
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

echo "=== Method 1: Compare full MD5 checksums with relative file paths ==="
find "$dir1" -type f ! -name '.DS_Store' -exec md5 {} + | sed "s|$dir1/||" | sort > "$tmpdir/checksums1.txt"
find "$dir2" -type f ! -name '.DS_Store' -exec md5 {} + | sed "s|$dir2/||" | sort > "$tmpdir/checksums2.txt"
diff "$tmpdir/checksums1.txt" "$tmpdir/checksums2.txt" || true

echo -e "\n=== Method 2: Compare only content hashes (ignoring file paths) ==="
find "$dir1" -type f ! -name '.DS_Store' -exec md5 {} + | awk '{print $NF}' | sort > "$tmpdir/hashes_m2_1.txt"
find "$dir2" -type f ! -name '.DS_Store' -exec md5 {} + | awk '{print $NF}' | sort > "$tmpdir/hashes_m2_2.txt"
diff "$tmpdir/hashes_m2_1.txt" "$tmpdir/hashes_m2_2.txt" || true

echo -e "\n=== Method 3: Exclude .DS_Store and AppleDouble (._*) files, compare hashes ==="
find "$dir1" -type f ! -name '.DS_Store' ! -name '._*' -exec md5 {} + | awk '{print $NF}' | sort > "$tmpdir/hashes_m3_1.txt"
find "$dir2" -type f ! -name '.DS_Store' ! -name '._*' -exec md5 {} + | awk '{print $NF}' | sort > "$tmpdir/hashes_m3_2.txt"
diff "$tmpdir/hashes_m3_1.txt" "$tmpdir/hashes_m3_2.txt" || true

echo -e "\n=== Method 4: Recursively compare directories and suppress AppleDouble file differences ==="
diff -rq "$dir1" "$dir2" | grep -v '/\._' || true
