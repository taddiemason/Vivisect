#!/bin/bash
# USB HID Keyboard Mode Setup for Vivisect
# Configures Raspberry Pi as USB HID Keyboard for automated keystroke injection
#
# ⚠️  WARNING ⚠️
# HID mode enables automated keystroke injection (BadUSB functionality).
# ONLY use for:
# - Authorized security testing and penetration testing
# - Digital forensics and incident response (with permission)
# - CTF competitions and security research
# - Educational purposes on systems you own
#
# NEVER use on systems without explicit written authorization.
# Unauthorized access is illegal and unethical.

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${RED}================================================================${NC}"
echo -e "${RED}  ⚠️  USB HID KEYBOARD MODE SETUP - AUTHORIZATION REQUIRED ⚠️${NC}"
echo -e "${RED}================================================================${NC}"
echo ""
echo -e "${YELLOW}This mode enables automated keystroke injection.${NC}"
echo -e "${YELLOW}Use ONLY for authorized security testing and forensics.${NC}"
echo ""
echo -e "${RED}By continuing, you confirm:${NC}"
echo -e "  1. You have explicit written authorization"
echo -e "  2. This is for legitimate security testing or forensics"
echo -e "  3. You understand legal and ethical implications"
echo ""
read -p "Do you have authorization to use HID mode? (yes/NO) " -r
echo
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Setup cancelled. HID mode NOT configured."
    exit 0
fi

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Error: This script must be run as root (use sudo)"
    exit 1
fi

# Detect Raspberry Pi model
PI_MODEL=$(cat /proc/device-tree/model 2>/dev/null || echo "Unknown")
echo "Detected: $PI_MODEL"
echo ""

if [[ "$PI_MODEL" != *"Raspberry Pi"* ]]; then
    echo "Warning: This script is designed for Raspberry Pi"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
fi

echo "[1/6] Installing required packages..."
apt-get update -qq
apt-get install -y python3 python3-pip

echo "[2/6] Configuring boot files..."

# Backup existing files
cp /boot/config.txt /boot/config.txt.backup 2>/dev/null || true
cp /boot/cmdline.txt /boot/cmdline.txt.backup 2>/dev/null || true

# Add dwc2 overlay to config.txt
if ! grep -q "dtoverlay=dwc2" /boot/config.txt 2>/dev/null; then
    echo "" >> /boot/config.txt
    echo "# USB HID Keyboard Mode for Vivisect" >> /boot/config.txt
    echo "dtoverlay=dwc2" >> /boot/config.txt
    echo "✓ Added dtoverlay=dwc2 to /boot/config.txt"
else
    echo "○ dtoverlay=dwc2 already configured"
fi

# Add dwc2 to modules (remove other gadgets)
if [ -f /boot/cmdline.txt ]; then
    # Remove old gadget modules
    sed -i 's/modules-load=dwc2,[^ ]*//' /boot/cmdline.txt

    if ! grep -q "modules-load=dwc2" /boot/cmdline.txt; then
        sed -i 's/rootwait/rootwait modules-load=dwc2/' /boot/cmdline.txt
        echo "✓ Added modules-load=dwc2 to /boot/cmdline.txt"
    else
        echo "○ modules-load already configured"
    fi
fi

echo "[3/6] Creating HID gadget configuration script..."

# Create script to setup HID via configfs
cat > /usr/local/bin/setup-hid-gadget <<'HIDEOF'
#!/bin/bash
# Setup USB HID Keyboard Gadget via ConfigFS

modprobe libcomposite
cd /sys/kernel/config/usb_gadget/ || exit 1

# Create gadget
mkdir -p vivisect_hid
cd vivisect_hid || exit 1

# Configure USB device
echo 0x1d6b > idVendor  # Linux Foundation
echo 0x0104 > idProduct # Multifunction Composite Gadget
echo 0x0100 > bcdDevice # v1.0.0
echo 0x0200 > bcdUSB    # USB 2.0

# Create English strings
mkdir -p strings/0x409
echo "fedcba9876543210" > strings/0x409/serialnumber
echo "Vivisect" > strings/0x409/manufacturer
echo "Forensics HID Keyboard" > strings/0x409/product

# Create HID function
mkdir -p functions/hid.usb0
echo 1 > functions/hid.usb0/protocol  # Keyboard
echo 1 > functions/hid.usb0/subclass  # Boot Interface Subclass
echo 8 > functions/hid.usb0/report_length

# HID Report Descriptor for keyboard
echo -ne \\x05\\x01\\x09\\x06\\xa1\\x01\\x05\\x07\\x19\\xe0\\x29\\xe7\\x15\\x00\\x25\\x01\\x75\\x01\\x95\\x08\\x81\\x02\\x95\\x01\\x75\\x08\\x81\\x03\\x95\\x05\\x75\\x01\\x05\\x08\\x19\\x01\\x29\\x05\\x91\\x02\\x95\\x01\\x75\\x03\\x91\\x03\\x95\\x06\\x75\\x08\\x15\\x00\\x25\\x65\\x05\\x07\\x19\\x00\\x29\\x65\\x81\\x00\\xc0 > functions/hid.usb0/report_desc

# Create configuration
mkdir -p configs/c.1/strings/0x409
echo "HID Keyboard Configuration" > configs/c.1/strings/0x409/configuration
echo 250 > configs/c.1/MaxPower

# Link function to configuration
ln -s functions/hid.usb0 configs/c.1/

# Find UDC and enable gadget
UDC_DEVICE=$(ls /sys/class/udc | head -1)
echo "$UDC_DEVICE" > UDC

echo "HID Keyboard gadget configured successfully"
echo "Device available at: /dev/hidg0"
HIDEOF

chmod +x /usr/local/bin/setup-hid-gadget

echo "✓ Created HID gadget setup script"

echo "[4/6] Creating systemd service..."

cat > /etc/systemd/system/vivisect-hid.service <<'EOF'
[Unit]
Description=Vivisect USB HID Keyboard Gadget
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/setup-hid-gadget
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable vivisect-hid.service

echo "✓ Created and enabled systemd service"

echo "[5/6] Creating payload directory..."

mkdir -p /var/lib/vivisect/hid_payloads
chown -R $(logname 2>/dev/null || echo $SUDO_USER):$(logname 2>/dev/null || echo $SUDO_USER) /var/lib/vivisect/hid_payloads 2>/dev/null || true

# Create example payload
cat > /var/lib/vivisect/hid_payloads/example_windows_triage.txt <<'EOF'
# Vivisect HID Payload - Windows Triage
# This payload opens Command Prompt and runs system

 information commands
#
# Format: One command per line
# Use [DELAY:ms] for delays
# Use [GUI+r] for Windows key + R

[DELAY:2000]
[GUI+r]
[DELAY:500]
cmd
[ENTER]
[DELAY:1000]
systeminfo > C:\temp\vivisect_triage.txt
[ENTER]
[DELAY:2000]
ipconfig /all >> C:\temp\vivisect_triage.txt
[ENTER]
[DELAY:1000]
netstat -ano >> C:\temp\vivisect_triage.txt
[ENTER]
[DELAY:1000]
tasklist /v >> C:\temp\vivisect_triage.txt
[ENTER]
[DELAY:1000]
exit
[ENTER]
EOF

echo "✓ Created payload directory and example payloads"

echo "[6/6] Security warnings and logging..."

# Log HID setup to syslog
logger -t vivisect-hid "USB HID keyboard mode configured by $(logname 2>/dev/null || echo $SUDO_USER) at $(date)"

echo ""
echo -e "${GREEN}================================================================${NC}"
echo -e "${GREEN}  USB HID Keyboard Mode Setup Complete!${NC}"
echo -e "${GREEN}================================================================${NC}"
echo ""
echo "Configuration:"
echo "  Mode: HID Keyboard (Keystroke Injection)"
echo "  Device: /dev/hidg0"
echo "  Payloads: /var/lib/vivisect/hid_payloads/"
echo ""
echo -e "${YELLOW}⚠️  SECURITY WARNINGS:${NC}"
echo "  1. HID mode enables automated keystroke injection"
echo "  2. This has been logged to syslog"
echo "  3. Use ONLY with explicit authorization"
echo "  4. Unauthorized use may be illegal"
echo ""
echo "Usage:"
echo "  1. Create payload in /var/lib/vivisect/hid_payloads/"
echo "  2. Connect device to target PC via USB"
echo "  3. Execute payload via Vivisect CLI or GUI"
echo ""
echo -e "${RED}IMPORTANT: You must REBOOT for changes to take effect!${NC}"
echo ""
read -p "Reboot now? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Rebooting in 3 seconds..."
    sleep 3
    reboot
else
    echo "Please reboot manually when ready: sudo reboot"
fi
