#!/usr/bin/env bash
# dumb read-only pi image grabber and analysis script
# collect a full image from a block device, mount boot partition read-only,
# runs file / strings / binwalk on boot blobs, compute hashes, and logs
set -euo pipefail

log() { printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*"; }

# ensure we have required commands
for cmd in dd losetup kpartx mount umount file strings binwalk sha256sum df awk; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Required command not found: $cmd. Install before running." >&2
    exit 1
  fi
done

echo "Pi Forensics artifact collection (read-only)."
read -r -p "Block device to image (eg /dev/mmcblk0 or /dev/sdX): " DEVICE
if [ -z "$DEVICE" ]; then
  echo "No device given." >&2
  exit 1
fi

echo "You entered: $DEVICE"
read -r -p "Type the device path again to confirm: " CONF
if [ "$CONF" != "$DEVICE" ]; then
  echo "Device confirmation mismatch. Aborting." >&2
  exit 1
fi

# Get device size
if ! DEV_BYTES=$(blockdev --getsize64 "$DEVICE" 2>/dev/null); then
  echo "Unable to determine device size with blockdev. Aborting." >&2
  exit 1
fi
# require 3x free space
FREE_BYTES=$(df --output=avail -B1 . | tail -1)
NEEDED=$(( DEV_BYTES * 3 ))
if [ "$FREE_BYTES" -lt "$NEEDED" ]; then
  echo "Not enough free disk space in cwd. Need at least 3× device size. Aborting." >&2
  exit 1
fi

TS=$(date -u +"%Y%m%dT%H%M%SZ")
ROOT="output/$TS"
IMAGES_DIR="$ROOT/images"
BOOT_MOUNT="$ROOT/boot_partition"
BOOT_COPY="$ROOT/boot_partition_copy"
ANALYSIS_DIR="$ROOT/analysis"
BINWALK_DIR="$ANALYSIS_DIR/binwalk"
STRINGS_DIR="$ANALYSIS_DIR/strings"
HASHES_DIR="$ANALYSIS_DIR/hashes"
LOGS_DIR="$ROOT/logs"
mkdir -p "$IMAGES_DIR" "$BOOT_MOUNT" "$BOOT_COPY" "$BINWALK_DIR" "$STRINGS_DIR" "$HASHES_DIR" "$LOGS_DIR"
LOGFILE="$LOGS_DIR/run.log"

# Start logging all output
exec > >(tee -a "$LOGFILE") 2>&1
set -x

IMG="$IMAGES_DIR/pi_backup.img"

# Read-only dd from device to image
log "Starting read-only image of $DEVICE to $IMG"
dd if="$DEVICE" of="$IMG" bs=4M status=progress conv=sync || { log "dd failed"; exit 1; }

log "Computing SHA256 of image"
sha256sum "$IMG" > "$HASHES_DIR/image_sha256.txt"

# Setup loop device and map partitions with kpartx
log "Setting up loop device and partition mapping"
LOOP=$(losetup -f --show "$IMG")
kpartx -av "$LOOP"

# Wait for partition devices; typically ${LOOP}p1 etc, but kpartx maps /dev/mapper/loopNp1
sleep 1

# Find boot partition mapper device: usually *p1 or partition with FAT
BOOT_PART=""
for dev in /dev/mapper/*; do
  if [ -b "$dev" ]; then
    # check filesystem type
    if file -s "$dev" | grep -i "FAT" >/dev/null 2>&1; then
      BOOT_PART="$dev"
      break
    fi
  fi
done

if [ -z "$BOOT_PART" ]; then
  log "Could not find FAT boot partition in image. Cleaning up."
  kpartx -d "$LOOP"
  losetup -d "$LOOP"
  exit 1
fi

log "Mounting boot partition ($BOOT_PART) read-only to $BOOT_MOUNT"
mount -o ro "$BOOT_PART" "$BOOT_MOUNT"

# Copy boot partition files into boot_partition_copy for analysis (do not preserve special files)
log "Copying boot partition to $BOOT_COPY for analysis (read-only source)"
cp -a "$BOOT_MOUNT/." "$BOOT_COPY/"

# Compute per-file sha256 for files of interest
for f in start.elf bootcode.bin fixup.dat fixup_cd.dat config.txt; do
  if [ -f "$BOOT_COPY/$f" ]; then
    sha256sum "$BOOT_COPY/$f" >> "$HASHES_DIR/boot_sha256.txt" || true
  fi
done

# Run file, strings and binwalk -e on known blobs
for f in start.elf bootcode.bin fixup.dat fixup_cd.dat; do
  if [ -f "$BOOT_COPY/$f" ]; then
    file "$BOOT_COPY/$f" > "$BINWALK_DIR/${f}.file" || true
    strings -n 8 "$BOOT_COPY/$f" > "$STRINGS_DIR/${f}.txt" || true
    # binwalk extraction - guard with timeout / small size
    binwalk -e "$BOOT_COPY/$f" -C "$BINWALK_DIR/${f}.ex" || true
  fi
done

# Create combined summary
echo "Combined strings summary" > "$ANALYSIS_DIR/summary.txt"
for s in "$STRINGS_DIR"/*.txt; do
  [ -f "$s" ] || continue
  echo "---- $s ----" >> "$ANALYSIS_DIR/summary.txt"
  head -n 200 "$s" >> "$ANALYSIS_DIR/summary.txt"
done

log "Syncing and unmounting boot partition"
sync
umount "$BOOT_MOUNT" || true
kpartx -d "$LOOP"
losetup -d "$LOOP"

log "Done. Outputs in $ROOT"
set +x
