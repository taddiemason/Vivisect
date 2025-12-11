#!/bin/bash
# Vivisect Digital Forensics Suite - Uninstallation Script

set -e

echo "================================================================"
echo "  Vivisect Digital Forensics Suite - Uninstallation"
echo "================================================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Error: This script must be run as root (use sudo)"
    exit 1
fi

read -p "Are you sure you want to uninstall Vivisect? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Uninstallation cancelled."
    exit 0
fi

echo "[1/5] Stopping and disabling service..."
systemctl stop vivisect.service 2>/dev/null || true
systemctl disable vivisect.service 2>/dev/null || true

echo "[2/5] Removing systemd service..."
rm -f /etc/systemd/system/vivisect.service
systemctl daemon-reload

echo "[3/5] Removing Vivisect files..."
rm -rf /opt/vivisect
rm -f /usr/local/bin/vivisect
rm -f /usr/local/bin/vivisect-daemon

echo "[4/5] Removing configuration..."
read -p "Remove configuration and data? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf /etc/vivisect
    rm -rf /var/lib/vivisect
    rm -rf /var/log/vivisect
    echo "Configuration and data removed."
else
    echo "Configuration and data preserved."
fi

echo "[5/5] Cleanup complete."

echo ""
echo "================================================================"
echo "  Vivisect has been uninstalled"
echo "================================================================"
