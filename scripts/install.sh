#!/bin/bash
# Vivisect Digital Forensics Suite - Installation Script
# For Debian-based systems

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

echo "[2/7] Installing core system dependencies..."
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

echo "[3/9] Installing forensics tools (optional, may skip if unavailable)..."
# These may not be available on all systems, so we use || true
apt-get install -y foremost || echo "Warning: foremost not available"
apt-get install -y scalpel || echo "Warning: scalpel not available"
apt-get install -y dcfldd || echo "Warning: dcfldd not available (dd will be used as fallback)"
apt-get install -y sleuthkit || echo "Warning: sleuthkit not available"
apt-get install -y binwalk || echo "Warning: binwalk not available"
apt-get install -y exiftool || echo "Warning: exiftool not available"
apt-get install -y yara || echo "Warning: yara not available"

# Optional advanced tools
echo "[4/9] Installing optional advanced forensics tools..."
apt-get install -y autopsy || echo "Warning: autopsy not available"
apt-get install -y guymager || echo "Warning: guymager not available"
apt-get install -y bulk-extractor || echo "Warning: bulk-extractor not available"
apt-get install -y clamav || echo "Warning: clamav not available"
apt-get install -y chkrootkit || echo "Warning: chkrootkit not available"
apt-get install -y rkhunter || echo "Warning: rkhunter not available"
apt-get install -y lynis || echo "Warning: lynis not available"

# Note: volatility is typically installed via pip, not apt
echo "Note: Volatility 3 can be installed via pip with: pip3 install volatility3"

# GUI dependencies (try both old and new package names)
echo "[5/9] Installing GUI dependencies (optional)..."
apt-get install -y chromium-browser || apt-get install -y chromium || echo "Warning: chromium not available"
apt-get install -y x11-xserver-utils unclutter xinit xorg || echo "Warning: some GUI packages not available"

echo "[6/9] Installing Python dependencies..."
pip3 install --upgrade pip
pip3 install -r requirements.txt

echo "[7/9] Creating directories and setting up Vivisect..."
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

echo "[8/9] Setting up systemd services..."
if [ -f systemd/vivisect.service ]; then
    cp systemd/vivisect.service /etc/systemd/system/
fi
if [ -f systemd/vivisect-gui.service ]; then
    cp systemd/vivisect-gui.service /etc/systemd/system/
fi
systemctl daemon-reload

echo "[9/9] Configuring services and final setup..."
# Enable CLI service if systemd file exists
if [ -f /etc/systemd/system/vivisect.service ]; then
    systemctl enable vivisect.service || echo "Warning: Could not enable vivisect service"
fi

echo ""
echo "GUI Setup:"
if [ -f /etc/systemd/system/vivisect-gui.service ]; then
    read -p "Do you want to enable GUI kiosk mode on boot? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        systemctl enable vivisect-gui.service
        echo "✓ GUI kiosk mode will launch on boot"
    else
        echo "○ GUI kiosk mode disabled (you can start manually with: vivisect-gui)"
    fi
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
