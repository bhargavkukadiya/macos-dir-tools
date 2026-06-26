#!/bin/bash
set -euo pipefail

# dir_stats.sh
# --------------------------------------
# Displays disk usage statistics for a directory, broken down by file type.
# Automatically excludes macOS metadata files (.DS_Store, ._*).
#
# Usage:
#   chmod +x dir_stats.sh
#   ./dir_stats.sh /path/to/folder [options]
#
# Options:
#   -n, --top <N>       Show top N file types (default: 10)
#   -a, --all           Include hidden files
#   --no-color          Disable colored output

# --- Color Support ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
RESET='\033[0m'

# --- Defaults ---
top_n=10
include_hidden=false
use_color=true

# --- Parse Arguments ---
usage() {
    cat <<EOF
Usage: $(basename "$0") <directory> [options]

Options:
  -n, --top <N>     Show top N file types (default: 10)
  -a, --all         Include hidden files and directories
  --no-color        Disable colored output
  -h, --help        Show this help message
EOF
    exit 0
}

positional=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        -n|--top)
            top_n="$2"
            shift 2
            ;;
        -a|--all)
            include_hidden=true
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

if [[ ${#positional[@]} -lt 1 ]]; then
    echo "Error: Directory path required." >&2
    echo "Run '$(basename "$0") --help' for usage." >&2
    exit 1
fi

target_dir="${positional[0]}"
[[ -d "$target_dir" ]] || { echo "Error: '$target_dir' is not a directory" >&2; exit 1; }

target_dir=$(cd "$target_dir" && pwd)

if [[ "$use_color" == false ]] || [[ ! -t 1 ]]; then
    RED='' GREEN='' YELLOW='' CYAN='' BOLD='' DIM='' RESET=''
fi

# --- Helper: Format Size ---
format_size() {
    local bytes=$1
    if [[ $bytes -ge 1073741824 ]]; then
        printf "%.1f GB" "$(echo "scale=1; $bytes / 1073741824" | bc)"
    elif [[ $bytes -ge 1048576 ]]; then
        printf "%.1f MB" "$(echo "scale=1; $bytes / 1048576" | bc)"
    elif [[ $bytes -ge 1024 ]]; then
        printf "%.1f KB" "$(echo "scale=1; $bytes / 1024" | bc)"
    else
        printf "%d B" "$bytes"
    fi
}

# --- Build find command ---
find_args=("$target_dir" -type f ! -name '.DS_Store' ! -name '._*')
if [[ "$include_hidden" == false ]]; then
    find_args+=( ! -path '*/\.*')
fi

# --- Collect Stats ---
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

# Get all file sizes and extensions
find "${find_args[@]}" -exec stat -f '%z %N' {} + 2>/dev/null | while IFS=' ' read -r size filepath; do
    filename=$(basename "$filepath")
    if [[ "$filename" == *.* ]]; then
        ext=".${filename##*.}"
        ext=$(echo "$ext" | tr '[:upper:]' '[:lower:]')
    else
        ext="(no extension)"
    fi
    echo "$size $ext"
done > "$tmpdir/files.txt"

# Total stats
total_files=$(wc -l < "$tmpdir/files.txt" | tr -d ' ')
total_size=$(awk '{sum += $1} END {print sum+0}' "$tmpdir/files.txt")

# Count directories
total_dirs=$(find "$target_dir" -type d | wc -l | tr -d ' ')
total_dirs=$((total_dirs - 1))  # exclude the root dir itself

# Stats by extension
awk '{ext=$2; sizes[ext]+=$1; counts[ext]++}
     END {for (e in sizes) printf "%d %d %s\n", sizes[e], counts[e], e}' \
    "$tmpdir/files.txt" | sort -rn > "$tmpdir/by_ext.txt"

# --- Output ---
echo -e "${BOLD}${CYAN}📊 Directory Statistics${RESET}"
echo -e "${DIM}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo -e "  ${BOLD}Path:${RESET}    $target_dir"
echo -e "  ${BOLD}Files:${RESET}   $total_files"
echo -e "  ${BOLD}Folders:${RESET} $total_dirs"
echo -e "  ${BOLD}Total:${RESET}   $(format_size "$total_size")"
echo -e "${DIM}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"

if [[ "$total_files" -eq 0 ]]; then
    echo -e "\n${YELLOW}No files found.${RESET}"
    exit 0
fi

echo -e "\n${BOLD}Top ${top_n} File Types by Size:${RESET}\n"
printf "  ${DIM}%-18s %10s %8s %8s${RESET}\n" "Extension" "Size" "Files" "% Size"
printf "  ${DIM}%-18s %10s %8s %8s${RESET}\n" "──────────────────" "──────────" "────────" "────────"

count=0
while IFS=' ' read -r size file_count ext; do
    [[ -z "$size" ]] && continue
    count=$((count + 1))
    [[ $count -gt $top_n ]] && break

    if [[ $total_size -gt 0 ]]; then
        pct=$(echo "scale=1; $size * 100 / $total_size" | bc)
    else
        pct="0.0"
    fi

    formatted_size=$(format_size "$size")

    # Color based on size percentage
    if (( $(echo "$pct > 50" | bc -l) )); then
        color="$RED"
    elif (( $(echo "$pct > 20" | bc -l) )); then
        color="$YELLOW"
    else
        color="$GREEN"
    fi

    printf "  ${color}%-18s %10s %8d %7s%%${RESET}\n" "$ext" "$formatted_size" "$file_count" "$pct"
done < "$tmpdir/by_ext.txt"

remaining_types=$(( $(wc -l < "$tmpdir/by_ext.txt" | tr -d ' ') - top_n ))
if [[ $remaining_types -gt 0 ]]; then
    echo -e "\n  ${DIM}...and $remaining_types more file type(s)${RESET}"
fi

echo ""
