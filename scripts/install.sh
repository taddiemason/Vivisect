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
echo "[3/7] Installing optional forensics tools..."
apt-get install -y \
    autopsy \
    guymager \
    bulk-extractor \
    yara \
    clamav \
    chkrootkit \
    rkhunter \
    lynis || true

echo "[4/7] Installing Python dependencies..."
pip3 install -r requirements.txt

echo "[5/7] Creating directories and setting up Vivisect..."
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
chmod +x scripts/vivisect-daemon

# Install daemon script
cp scripts/vivisect-daemon /usr/local/bin/
chmod +x /usr/local/bin/vivisect-daemon

# Create symlink for easy access
ln -sf "$INSTALL_DIR/src/main.py" /usr/local/bin/vivisect
chmod +x /usr/local/bin/vivisect

echo "[6/7] Setting up systemd service..."
cp systemd/vivisect.service /etc/systemd/system/
systemctl daemon-reload

echo "[7/7] Configuring auto-start..."
systemctl enable vivisect.service

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
echo "Commands:"
echo "  vivisect --help           Show help"
echo "  vivisect collect <case>   Run full collection"
echo "  systemctl start vivisect  Start service"
echo "  systemctl status vivisect Check service status"
echo ""
echo "To start Vivisect now:"
echo "  systemctl start vivisect"
echo ""
echo "The service is configured to auto-start on boot."
echo "================================================================"
