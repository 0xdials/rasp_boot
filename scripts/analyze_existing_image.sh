#!/usr/bin/env bash
# helper script to analyze an existing disk image (skips imaging)
# mounts boot partition read-only, runs file/strings/binwalk, hashes boot files
# cleans up loop devices and mounts on exit
# mainly written to stop needing to reimage everytime i tested, should probably have this as an option in collect_artifacts.sh

set -Eeuo pipefail
trap 'echo "error at line $LINENO"; cleanup; exit 1' ERR INT TERM

IMAGE_PATH=""
MOUNT_POINT="/tmp/boot_mount"
OUTPUT_DIR=""
LOOP_DEV=""

cleanup() {
  set +e
  if mountpoint -q "$MOUNT_POINT"; then
    umount "$MOUNT_POINT"
  fi
  if [ -n "$LOOP_DEV" ]; then
    kpartx -d "$LOOP_DEV"
    losetup -d "$LOOP_DEV"
  fi
  rmdir "$MOUNT_POINT" 2>/dev/null || true
}
log() {
  printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*"
}

if [ $# -ne 1 ]; then
  echo "usage: $0 /path/to/image.img"
  exit 2
fi

IMAGE_PATH="$1"
if [ ! -f "$IMAGE_PATH" ]; then
  echo "image file not found: $IMAGE_PATH"
  exit 1
fi

TIMESTAMP=$(date -u +%Y%m%dT%H%M%SZ)
OUTPUT_DIR="output/${TIMESTAMP}"
mkdir -p "$OUTPUT_DIR"/{images,analysis/strings,analysis/binwalk,analysis/hashes}

if [ -n "$SUDO_USER" ]; then
  chown "$SUDO_USER":"$SUDO_USER" "$OUTPUT_DIR" "$OUTPUT_DIR"/{images,analysis,analysis/strings,analysis/binwalk,analysis/hashes} || true
fi

log "Setting up loop device for image $IMAGE_PATH"
LOOP_DEV=$(losetup -f --show "$IMAGE_PATH")
log "Loop device is $LOOP_DEV"

log "Creating partition mappings"
kpartx -av "$LOOP_DEV"
sleep 2  # give partitions time to settle

# find boot partition (FAT)
BOOT_PART=""
for dev in /dev/mapper/*; do
  if [ ! -b "$dev" ]; then
    continue
  fi
  resolved=$(readlink -f "$dev")
  if file -s "$resolved" | grep -iq FAT; then
    BOOT_PART="$dev"
    break
  fi
done

if [ -z "$BOOT_PART" ]; then
  log "Could not find FAT boot partition in image. Cleaning up."
  cleanup
  exit 1
fi

log "Boot partition found: $BOOT_PART"

mkdir -p "$MOUNT_POINT"
log "Mounting boot partition read-only at $MOUNT_POINT"
mount -o ro "$BOOT_PART" "$MOUNT_POINT"

log "Copying boot partition files for processing"
BOOT_COPY_DIR="$OUTPUT_DIR/boot_partition_copy"
mkdir -p "$BOOT_COPY_DIR"
cp -a "$MOUNT_POINT"/. "$BOOT_COPY_DIR"/

log "Running analysis recursively on boot files"
find "$BOOT_COPY_DIR" -type f | while read -r f; do
  base=$(basename "$f")
  file "$f" >"$OUTPUT_DIR/analysis/strings/${base}_file.txt"
  strings "$f" >"$OUTPUT_DIR/analysis/strings/${base}_strings.txt"
  binwalk -q -l "$OUTPUT_DIR/analysis/binwalk/${base}.json" "$f"
done

log "Computing hashes recursively on boot files"
HASHES_FILE="$OUTPUT_DIR/analysis/hashes/boot_sha256.txt"
find "$BOOT_COPY_DIR" -type f | while read -r f; do
  sha256sum "$f" >>"$HASHES_FILE"
done

log "Analysis complete. Outputs in $OUTPUT_DIR"

cleanup
