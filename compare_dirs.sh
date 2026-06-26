#!/bin/bash
set -euo pipefail

# compare_dirs.sh
# --------------------------------------
# Compares the contents of two directories using four different methods,
# handling macOS metadata files like .DS_Store and AppleDouble files (._*).
#
# Supports both macOS (md5) and Linux (md5sum) automatically.
#
# Usage:
#   chmod +x compare_dirs.sh
#   ./compare_dirs.sh <dir1> <dir2> [options]
#
# Options:
#   -m, --method <1|2|3|4>  Run only the specified method (default: all)
#   -q, --quiet             Only show differences, suppress headers when clean
#   --no-color              Disable colored output

# --- Color Support ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
RESET='\033[0m'

# --- Defaults ---
method="all"
quiet=false
use_color=true
has_diff=false

# --- Parse Arguments ---
usage() {
    cat <<EOF
Usage: $(basename "$0") <dir1> <dir2> [options]

Options:
  -m, --method <1|2|3|4>  Run only the specified method (default: all)
  -q, --quiet             Only show differences, suppress headers when clean
  --no-color              Disable colored output
  -h, --help              Show this help message

Methods:
  1  Compare full MD5 checksums with relative file paths
  2  Compare only content hashes, ignoring file paths
  3  Like method 2, but also excludes AppleDouble (._*) files
  4  Recursive diff, suppressing AppleDouble file differences
EOF
    exit 0
}

# Positional args
positional=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        -m|--method)
            method="$2"
            shift 2
            ;;
        -q|--quiet)
            quiet=true
            shift
            ;;
        --no-color)
            use_color=false
            shift
            ;;
        -h|--help)
            usage
            ;;
        -*)
            echo "Error: Unknown option '$1'" >&2
            echo "Run '$(basename "$0") --help' for usage." >&2
            exit 1
            ;;
        *)
            positional+=("$1")
            shift
            ;;
    esac
done

# Disable color if not a terminal or --no-color
if [[ "$use_color" == false ]] || [[ ! -t 1 ]]; then
    RED='' GREEN='' YELLOW='' CYAN='' BOLD='' DIM='' RESET=''
fi

# Validate positional args
if [[ ${#positional[@]} -lt 2 ]]; then
    echo "Error: Two directories required." >&2
    echo "Run '$(basename "$0") --help' for usage." >&2
    exit 1
fi

dir1="${positional[0]}"
dir2="${positional[1]}"

[[ -d "$dir1" ]] || { echo "Error: '$dir1' is not a directory" >&2; exit 1; }
[[ -d "$dir2" ]] || { echo "Error: '$dir2' is not a directory" >&2; exit 1; }

# Validate method
if [[ "$method" != "all" && ! "$method" =~ ^[1-4]$ ]]; then
    echo "Error: Method must be 1, 2, 3, or 4 (got '$method')" >&2
    exit 1
fi

# Normalize to absolute paths
dir1=$(cd "$dir1" && pwd)
dir2=$(cd "$dir2" && pwd)

# --- Auto-detect Hash Command ---
if command -v md5 &>/dev/null; then
    # macOS: md5 outputs "MD5 (file) = hash"
    hash_cmd="md5"
    hash_extract="awk '{print \$NF}'"
elif command -v md5sum &>/dev/null; then
    # Linux: md5sum outputs "hash  file"
    hash_cmd="md5sum"
    hash_extract="awk '{print \$1}'"
else
    echo "Error: Neither 'md5' nor 'md5sum' found on this system." >&2
    exit 1
fi

# --- Temp Directory with Cleanup ---
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

# --- Helper Functions ---
print_header() {
    echo -e "\n${BOLD}${CYAN}=== $1 ===${RESET}"
}

print_result() {
    local diff_file="$1"
    local label="$2"
    if [[ -s "$diff_file" ]]; then
        has_diff=true
        echo -e "${RED}✗ Differences found:${RESET}"
        cat "$diff_file"
    else
        if [[ "$quiet" == false ]]; then
            echo -e "${GREEN}✓ ${label}${RESET}"
        fi
    fi
}

count_files() {
    local dir="$1"
    shift
    find "$dir" -type f "$@" | wc -l | tr -d ' '
}

# --- Methods ---
run_method_1() {
    if [[ "$quiet" == false ]] || [[ "$method" != "all" ]]; then
        print_header "Method 1: Compare MD5 checksums with relative file paths"
    fi

    if [[ "$hash_cmd" == "md5" ]]; then
        find "$dir1" -type f ! -name '.DS_Store' -exec md5 {} + | sed "s|$dir1/||" | sort > "$tmpdir/m1_1.txt"
        find "$dir2" -type f ! -name '.DS_Store' -exec md5 {} + | sed "s|$dir2/||" | sort > "$tmpdir/m1_2.txt"
    else
        (cd "$dir1" && find . -type f ! -name '.DS_Store' -exec md5sum {} +) | sort > "$tmpdir/m1_1.txt"
        (cd "$dir2" && find . -type f ! -name '.DS_Store' -exec md5sum {} +) | sort > "$tmpdir/m1_2.txt"
    fi

    diff "$tmpdir/m1_1.txt" "$tmpdir/m1_2.txt" > "$tmpdir/m1_diff.txt" 2>&1 || true
    print_result "$tmpdir/m1_diff.txt" "Directories match (checksums + paths)"
}

run_method_2() {
    if [[ "$quiet" == false ]] || [[ "$method" != "all" ]]; then
        print_header "Method 2: Compare content hashes only (ignoring paths)"
    fi

    find "$dir1" -type f ! -name '.DS_Store' -exec "$hash_cmd" {} + | eval "$hash_extract" | sort > "$tmpdir/m2_1.txt"
    find "$dir2" -type f ! -name '.DS_Store' -exec "$hash_cmd" {} + | eval "$hash_extract" | sort > "$tmpdir/m2_2.txt"

    diff "$tmpdir/m2_1.txt" "$tmpdir/m2_2.txt" > "$tmpdir/m2_diff.txt" 2>&1 || true
    print_result "$tmpdir/m2_diff.txt" "Content hashes match"
}

run_method_3() {
    if [[ "$quiet" == false ]] || [[ "$method" != "all" ]]; then
        print_header "Method 3: Compare hashes excluding .DS_Store and AppleDouble (._*)"
    fi

    find "$dir1" -type f ! -name '.DS_Store' ! -name '._*' -exec "$hash_cmd" {} + | eval "$hash_extract" | sort > "$tmpdir/m3_1.txt"
    find "$dir2" -type f ! -name '.DS_Store' ! -name '._*' -exec "$hash_cmd" {} + | eval "$hash_extract" | sort > "$tmpdir/m3_2.txt"

    diff "$tmpdir/m3_1.txt" "$tmpdir/m3_2.txt" > "$tmpdir/m3_diff.txt" 2>&1 || true
    print_result "$tmpdir/m3_diff.txt" "Content hashes match (excluding macOS metadata)"
}

run_method_4() {
    if [[ "$quiet" == false ]] || [[ "$method" != "all" ]]; then
        print_header "Method 4: Recursive diff (suppressing AppleDouble differences)"
    fi

    diff -rq "$dir1" "$dir2" 2>&1 | grep -v '/\._' > "$tmpdir/m4_diff.txt" || true
    print_result "$tmpdir/m4_diff.txt" "Directories are identical"
}

# --- Run ---
echo -e "${BOLD}Comparing:${RESET}"
echo -e "  ${DIM}L:${RESET} $dir1"
echo -e "  ${DIM}R:${RESET} $dir2"

count1=$(count_files "$dir1" ! -name '.DS_Store' ! -name '._*')
count2=$(count_files "$dir2" ! -name '.DS_Store' ! -name '._*')
echo -e "  ${DIM}Files: $count1 vs $count2 (excluding macOS metadata)${RESET}"

if [[ "$method" == "all" ]]; then
    run_method_1
    run_method_2
    run_method_3
    run_method_4
else
    eval "run_method_$method"
fi

# --- Summary ---
echo ""
if [[ "$has_diff" == true ]]; then
    echo -e "${RED}${BOLD}Result: Differences detected.${RESET}"
    exit 1
else
    echo -e "${GREEN}${BOLD}Result: Directories are identical.${RESET}"
    exit 0
fi
