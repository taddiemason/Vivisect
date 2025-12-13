#!/bin/bash
# Vivisect Digital Forensics Suite - Minimal Installation Script
# For Debian-based systems - Only installs core dependencies

set -e

# Colors for output
CYAN='\033[0;36m'
NC='\033[0m' # No Color

clear

echo -e "${CYAN}"
cat << "EOF"
    ____                       __  _
   / __/__ _____  ___ ____  __/ /_(_)______ _
  _\ \/ // / _ \/ -_)  _/ |/ / __/ / __/ _ `/
 /___/\_, /_//_/\__/_/  |___/\__/_/\__/\_,_/
     /___/

     Digital Forensics Suite - Powered by Vivisect
EOF
echo -e "${NC}"

echo "================================================================"
echo "  Vivisect Digital Forensics Suite - Minimal Installation"
echo "================================================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Error: This script must be run as root (use sudo)"
    exit 1
fi

echo "[1/6] Updating package lists..."
apt-get update -qq

echo "[2/6] Installing core system dependencies..."
# Only install packages that are commonly available
apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    tcpdump \
    tshark \
    wireshark-common \
    git \
    build-essential

# Install libmagic (try new t64 version first, fallback to old version)
apt-get install -y libmagic1t64 libmagic-dev || apt-get install -y libmagic1 libmagic-dev

echo "[3/6] Installing optional forensics tools (may skip if unavailable)..."
# Try to install these but don't fail if they're missing
apt-get install -y foremost || echo "Warning: foremost not available"
apt-get install -y scalpel || echo "Warning: scalpel not available"
apt-get install -y dcfldd || echo "Warning: dcfldd not available (using dd as fallback)"
apt-get install -y sleuthkit || echo "Warning: sleuthkit not available"
apt-get install -y binwalk || echo "Warning: binwalk not available"
apt-get install -y exiftool || echo "Warning: exiftool not available"

echo "[4/6] Installing Python dependencies..."
# Use --break-system-packages for Debian 12+ / Ubuntu 24.04+ (PEP 668)
pip3 install --upgrade pip --break-system-packages 2>/dev/null || pip3 install --upgrade pip
pip3 install -r requirements.txt --break-system-packages 2>/dev/null || pip3 install -r requirements.txt

echo "[5/6] Creating directories and setting up Vivisect..."
INSTALL_DIR="/opt/vivisect"
mkdir -p "$INSTALL_DIR"
mkdir -p /etc/vivisect
mkdir -p /var/lib/vivisect/output
mkdir -p /var/log/vivisect
mkdir -p /tmp/vivisect

# Copy files
echo "Copying Vivisect files..."
cp -r src "$INSTALL_DIR/"
[ -d config ] && cp -r config "$INSTALL_DIR/" || echo "No config directory found"
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
chmod +x "$INSTALL_DIR/src/main.py" 2>/dev/null || true
chmod +x "$INSTALL_DIR/src/web/run_server.py" 2>/dev/null || true

# Create symlink for easy access
ln -sf "$INSTALL_DIR/src/main.py" /usr/local/bin/vivisect 2>/dev/null || true
ln -sf "$INSTALL_DIR/src/web/run_server.py" /usr/local/bin/vivisect-gui 2>/dev/null || true

echo "[6/6] Setting up systemd services (optional)..."
if [ -d systemd ]; then
    cp systemd/vivisect.service /etc/systemd/system/ 2>/dev/null || true
    cp systemd/vivisect-gui.service /etc/systemd/system/ 2>/dev/null || true
    systemctl daemon-reload || true
fi

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
echo "Quick Start:"
echo "  1. Try the enhanced reporting demo:"
echo "     cd $INSTALL_DIR && python3 examples/demo_enhanced_reports.py"
echo ""
echo "  2. Start the web GUI:"
echo "     cd $INSTALL_DIR && python3 src/web/run_server.py"
echo "     Then open: http://localhost:5000"
echo ""
echo "  3. View generated reports:"
echo "     ls -lh /var/lib/vivisect/output/"
echo ""
echo "================================================================"
