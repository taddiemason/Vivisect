#!/bin/bash
# USB Mass Storage Sync Script for Vivisect
# Syncs reports and evidence to the USB mass storage backing file

set -e

STORAGE_FILE="/var/lib/vivisect/usb_storage.img"
STORAGE_MOUNT="/mnt/vivisect_usb"
OUTPUT_DIR="/var/lib/vivisect/output"
LOGFILE="/var/log/vivisect/usb-storage-sync.log"

mkdir -p /var/log/vivisect

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOGFILE"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Error: This script must be run as root (use sudo)"
    exit 1
fi

# Check if storage file exists
if [ ! -f "$STORAGE_FILE" ]; then
    log "ERROR: Mass storage backing file not found: $STORAGE_FILE"
    log "Run setup-usb-gadget.sh first to create it"
    exit 1
fi

# Mount the storage image
log "Mounting USB mass storage image..."
mkdir -p "$STORAGE_MOUNT"

if mountpoint -q "$STORAGE_MOUNT"; then
    log "Already mounted at $STORAGE_MOUNT"
else
    mount -o loop "$STORAGE_FILE" "$STORAGE_MOUNT"
    if [ $? -eq 0 ]; then
        log "✓ Mounted at $STORAGE_MOUNT"
    else
        log "ERROR: Failed to mount storage image"
        exit 1
    fi
fi

# Create directory structure
mkdir -p "$STORAGE_MOUNT/reports"
mkdir -p "$STORAGE_MOUNT/evidence"
mkdir -p "$STORAGE_MOUNT/logs"

# Sync reports
if [ -d "$OUTPUT_DIR/reports" ]; then
    log "Syncing reports..."
    rsync -av --update "$OUTPUT_DIR/reports/" "$STORAGE_MOUNT/reports/" >> "$LOGFILE" 2>&1
    REPORT_COUNT=$(find "$STORAGE_MOUNT/reports" -type f | wc -l)
    log "✓ Synced reports ($REPORT_COUNT files)"
else
    log "○ No reports directory found"
fi

# Sync evidence metadata (exclude large disk images)
if [ -d "$OUTPUT_DIR/evidence" ]; then
    log "Syncing evidence metadata..."
    rsync -av --update \
        --exclude '*.img' \
        --exclude '*.dd' \
        --exclude '*.raw' \
        --exclude '*.bin' \
        "$OUTPUT_DIR/evidence/" "$STORAGE_MOUNT/evidence/" >> "$LOGFILE" 2>&1
    EVIDENCE_COUNT=$(find "$STORAGE_MOUNT/evidence" -type f | wc -l)
    log "✓ Synced evidence metadata ($EVIDENCE_COUNT files)"
else
    log "○ No evidence directory found"
fi

# Copy recent logs
if [ -d "/var/log/vivisect" ]; then
    log "Syncing logs..."
    rsync -av --update \
        --max-size=10M \
        /var/log/vivisect/*.log "$STORAGE_MOUNT/logs/" >> "$LOGFILE" 2>&1 || true
    log "✓ Synced logs"
fi

# Create README file for the USB drive
cat > "$STORAGE_MOUNT/README.txt" <<EOF
Vivisect Forensics Suite - Evidence Storage
============================================

This USB drive contains forensic reports and evidence collected by Vivisect.

Directory Structure:
  /reports/   - Forensic analysis reports (HTML, JSON, text)
  /evidence/  - Evidence metadata and artifacts
  /logs/      - System logs from forensics collection

Note: Large disk images are not synced to this drive to save space.
Access full evidence via network connection (10.55.0.2) or serial console.

Last sync: $(date)

For more information: https://github.com/taddiemason/Vivisect
EOF

# Sync filesystem to ensure all writes are committed
log "Flushing filesystem..."
sync

# Get storage usage
USAGE=$(df -h "$STORAGE_MOUNT" | tail -1 | awk '{print $5}')
log "Storage usage: $USAGE"

# Unmount
log "Unmounting..."
umount "$STORAGE_MOUNT"

if [ $? -eq 0 ]; then
    log "✓ USB mass storage sync complete!"
else
    log "WARNING: Unmount had issues, but sync completed"
fi

log "Storage is ready for host PC access"
