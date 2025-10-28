#!/usr/bin/env bash
# build/merge a "known good" SHA256 baseline JSON from a directory of boot blobs.
# Usage:
#   scripts/update_baseline_from_dir.sh <dir> [--output data/known_hashes/raspi_boot_sha256.json] \
#       [--source "Raspberry Pi Firmware GitHub (latest)"] [--pattern "start.elf bootcode.bin fixup*.dat"] \
#       [--dry-run] [--no-merge]

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <dir> [--output path.json] [--source label] [--pattern \"g1 g2\"] [--dry-run] [--no-merge]" >&2
  exit 2
fi

DIR="$1"; shift || true
OUT="data/known_hashes/raspi_boot_sha256.json"
SOURCE="LOCAL-GENERATED"
PATTERNS=("start.elf" "bootcode.bin" "fixup*.dat" "fixup*.bin")
DRY_RUN=0
MERGE=1

while [[ $# -gt 0 ]]; do
  case "$1" in
    --output) OUT="$2"; shift 2;;
    --source) SOURCE="$2"; shift 2;;
    --pattern) IFS=' ' read -r -a PATTERNS <<< "$2"; shift 2;;
    --dry-run) DRY_RUN=1; shift;;
    --no-merge) MERGE=0; shift;;
    *) echo "Unknown arg: $1" >&2; exit 2;;
  esac
done

if ! command -v sha256sum >/dev/null 2>&1; then
  echo "sha256sum not found." >&2
  exit 1
fi
if [[ ! -d "$DIR" ]]; then
  echo "Directory not found: $DIR" >&2
  exit 1
fi

# gather files
mapfile -t FILES < <(
  for pat in "${PATTERNS[@]}"; do
    find "$DIR" -type f -name "$pat" -print
  done | sort -u
)
if [[ ${#FILES[@]} -eq 0 ]]; then
  echo "No files matched patterns (${PATTERNS[*]}) in: $DIR" >&2
  exit 3
fi

# temp file (use repo dir to avoid /tmp weirdness)
TMP=$(mktemp -p . baseline.XXXXXX)
trap 'rm -f "$TMP"' EXIT
: > "$TMP"  # ensure we can write

# hashes
for f in "${FILES[@]}"; do
  base="$(basename "$f")"
  sum="$(sha256sum "$f" | awk '{print $1}')"
  printf "%s %s\n" "$base" "$sum" >> "$TMP"
done

# python merge/write (args BEFORE heredoc; that was the bug)
JSON_OUT=$(python3 - "$TMP" "$OUT" "$SOURCE" "$MERGE" <<'PY'
import json, sys, os, collections
# argv: [script, tmp_path, out_path, source, merge_flag]
if len(sys.argv) < 5:
    raise SystemExit("args: TMP OUT SOURCE MERGE_FLAG")

tmp_path, out_path, source, merge_flag = sys.argv[1:5]
merge = (merge_flag == "1")

pairs = []
with open(tmp_path, 'r', encoding='utf-8') as fh:
    for line in fh:
        line = line.strip()
        if not line:
            continue
        base, sha = line.split()
        pairs.append((base, sha))

new_files = collections.OrderedDict(pairs)

data = {"source": source, "notes": "Known-good SHA256 for Raspberry Pi boot blobs.", "files": {}}
if merge and os.path.exists(out_path):
    try:
        with open(out_path, 'r', encoding='utf-8') as fh:
            existing = json.load(fh)
            if isinstance(existing, dict) and isinstance(existing.get("files"), dict):
                data = existing
    except Exception:
        pass

data["source"] = source
data.setdefault("files", {})
for k, v in new_files.items():
    data["files"][k] = v

print(json.dumps(data, indent=2))
PY
)

if [[ $DRY_RUN -eq 1 ]]; then
  echo "$JSON_OUT"
  exit 0
fi

mkdir -p "$(dirname "$OUT")"
printf "%s\n" "$JSON_OUT" > "$OUT"
echo "Baseline written to: $OUT"
awk '{printf "  %s -> %s\n",$1,$2}' "$TMP"
