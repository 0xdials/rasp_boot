#!/usr/bin/env bash
# Mount boot partition read-only from an existing image file
set -euo pipefail
if [ "$#" -ne 2 ]; then
  echo "Usage: $0 /path/to/image.img /path/to/mountpoint" >&2
  exit 2
fi
IMG="$1"
MNT="$2"
for cmd in losetup kpartx mount file; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Required: $cmd" >&2
    exit 1
  fi
done
LOOP=$(losetup -f --show "$IMG")
kpartx -av "$LOOP"
sleep 1
# gotta find which partition is the FAT boot one
BOOT_PART=""
for dev in /dev/mapper/*; do
  if [ -b "$dev" ]; then
    if file -s "$dev" | grep -i "FAT" >/dev/null 2>&1; then
      BOOT_PART="$dev"
      break
    fi
  fi
done
if [ -z "$BOOT_PART" ]; then
  echo "Boot partition not found" >&2
  kpartx -d "$LOOP"
  losetup -d "$LOOP"
  exit 1
fi
mkdir -p "$MNT"
mount -o ro "$BOOT_PART" "$MNT"
echo "Mounted $BOOT_PART read-only at $MNT"
echo "To unmount: umount $MNT && kpartx -d $LOOP && losetup -d $LOOP"
