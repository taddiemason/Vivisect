#!/bin/bash
# Vivisect Digital Forensics Suite - Installation Script
# For Debian-based systems

set -e

echo "================================================================"
echo "  Vivisect Digital Forensics Suite - Installation"
echo "================================================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Error: This script must be run as root (use sudo)"
    exit 1
fi

echo "[1/7] Updating package lists..."
apt-get update -qq

echo "[2/7] Installing system dependencies..."
apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    tcpdump \
    tshark \
    wireshark-common \
    foremost \
    scalpel \
    dcfldd \
    sleuthkit \
    libmagic1 \
    libmagic-dev \
    volatility \
    binwalk \
    exiftool \
    git \
    build-essential

# Optional tools
echo "[3/9] Installing optional forensics tools..."
apt-get install -y \
    autopsy \
    guymager \
    bulk-extractor \
    yara \
    clamav \
    chkrootkit \
    rkhunter \
    lynis || true

# GUI dependencies
echo "[4/9] Installing GUI dependencies..."
apt-get install -y \
    chromium-browser \
    x11-xserver-utils \
    unclutter \
    xinit \
    xorg || true

echo "[5/9] Installing Python dependencies..."
pip3 install -r requirements.txt

echo "[6/9] Creating directories and setting up Vivisect..."
INSTALL_DIR="/opt/vivisect"
mkdir -p "$INSTALL_DIR"
mkdir -p /etc/vivisect
mkdir -p /var/lib/vivisect/output
mkdir -p /var/log/vivisect
mkdir -p /tmp/vivisect

# Copy files
echo "Copying Vivisect files..."
cp -r src "$INSTALL_DIR/"
cp -r config "$INSTALL_DIR/"
cp requirements.txt "$INSTALL_DIR/"

# Create default configuration
if [ ! -f /etc/vivisect/vivisect.conf ]; then
    cat > /etc/vivisect/vivisect.conf <<EOF
{
    "output_dir": "/var/lib/vivisect/output",
    "log_dir": "/var/log/vivisect",
    "temp_dir": "/tmp/vivisect",
    "auto_start": true,
    "modules": {
        "disk_imaging": {"enabled": true},
        "file_analysis": {"enabled": true},
        "network_forensics": {"enabled": true},
        "memory_analysis": {"enabled": true},
        "artifact_extraction": {"enabled": true}
    }
}
EOF
fi

# Make scripts executable
chmod +x "$INSTALL_DIR/src/main.py"
chmod +x "$INSTALL_DIR/src/web/run_server.py"
chmod +x scripts/vivisect-daemon
chmod +x scripts/launch-gui-kiosk.sh

# Install daemon script
cp scripts/vivisect-daemon /usr/local/bin/
chmod +x /usr/local/bin/vivisect-daemon

# Install GUI launcher
cp scripts/launch-gui-kiosk.sh /usr/local/bin/launch-gui-kiosk
chmod +x /usr/local/bin/launch-gui-kiosk

# Create symlink for easy access
ln -sf "$INSTALL_DIR/src/main.py" /usr/local/bin/vivisect
chmod +x /usr/local/bin/vivisect

# Create symlink for web GUI
ln -sf "$INSTALL_DIR/src/web/run_server.py" /usr/local/bin/vivisect-gui
chmod +x /usr/local/bin/vivisect-gui

echo "[7/9] Setting up systemd services..."
cp systemd/vivisect.service /etc/systemd/system/
cp systemd/vivisect-gui.service /etc/systemd/system/
systemctl daemon-reload

echo "[8/9] Configuring services..."
# Enable CLI service
systemctl enable vivisect.service

echo ""
echo "GUI Setup:"
read -p "Do you want to enable GUI kiosk mode on boot? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    systemctl enable vivisect-gui.service
    echo "✓ GUI kiosk mode will launch on boot"
else
    echo "○ GUI kiosk mode disabled (you can start manually with: vivisect-gui)"
fi

echo "[9/9] Final setup..."

echo ""
echo "================================================================"
echo "  Installation Complete!"
echo "================================================================"
echo ""
echo "Vivisect has been installed to: $INSTALL_DIR"
echo "Configuration file: /etc/vivisect/vivisect.conf"
echo "Output directory: /var/lib/vivisect/output"
echo "Log directory: /var/log/vivisect"
echo ""
echo "CLI Commands:"
echo "  vivisect --help             Show help"
echo "  vivisect collect <case>     Run full collection"
echo "  systemctl start vivisect    Start backend service"
echo ""
echo "GUI Commands:"
echo "  vivisect-gui                Start web GUI server"
echo "  launch-gui-kiosk            Launch GUI in kiosk mode"
echo "  systemctl start vivisect-gui Start GUI kiosk on boot"
echo ""
echo "Access Web GUI:"
echo "  Browser: http://localhost:5000"
echo "  Kiosk Mode: Enabled on boot (if selected)"
echo ""
echo "The CLI service is configured to auto-start on boot."
echo "================================================================"
