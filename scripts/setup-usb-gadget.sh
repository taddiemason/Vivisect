#!/bin/bash
# USB Gadget Mode Setup for Vivisect
# Configures Raspberry Pi Zero/4 to act as USB Ethernet device

set -e

echo "================================================================"
echo "  Vivisect USB Gadget Mode Setup"
echo "================================================================"
echo ""

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
apt-get install -y dnsmasq nmap iptables-persistent

echo "[2/6] Configuring boot files..."

# Backup existing files
cp /boot/config.txt /boot/config.txt.backup 2>/dev/null || true
cp /boot/cmdline.txt /boot/cmdline.txt.backup 2>/dev/null || true

# Add dwc2 overlay to config.txt
if ! grep -q "dtoverlay=dwc2" /boot/config.txt 2>/dev/null; then
    echo "" >> /boot/config.txt
    echo "# USB Gadget Mode for Vivisect" >> /boot/config.txt
    echo "dtoverlay=dwc2" >> /boot/config.txt
    echo "✓ Added dtoverlay=dwc2 to /boot/config.txt"
else
    echo "○ dtoverlay=dwc2 already configured"
fi

# Add modules to cmdline.txt
if [ -f /boot/cmdline.txt ]; then
    if ! grep -q "modules-load=dwc2,g_ether" /boot/cmdline.txt; then
        # Insert after rootwait
        sed -i 's/rootwait/rootwait modules-load=dwc2,g_ether/' /boot/cmdline.txt
        echo "✓ Added modules-load to /boot/cmdline.txt"
    else
        echo "○ modules-load already configured"
    fi
fi

echo "[3/6] Creating network configuration..."

# Create usb0 network interface configuration
cat > /etc/network/interfaces.d/usb0 <<EOF
# USB Gadget Ethernet Interface
auto usb0
allow-hotplug usb0
iface usb0 inet static
    address 10.55.0.2
    netmask 255.255.255.0
    gateway 10.55.0.1
    post-up /usr/local/bin/usb-gadget-connected
EOF

echo "✓ Created usb0 interface configuration"

echo "[4/6] Creating USB connection detection script..."

cat > /usr/local/bin/usb-gadget-connected <<'EOF'
#!/bin/bash
# Triggered when USB gadget connects to host

LOGFILE="/var/log/vivisect/usb-gadget.log"
mkdir -p /var/log/vivisect

echo "[$(date)] USB Gadget connected to host" >> "$LOGFILE"

# Wait for interface to be fully up
sleep 2

# Start automatic forensics collection
if [ -x /usr/local/bin/vivisect ]; then
    echo "[$(date)] Starting automatic collection..." >> "$LOGFILE"

    # Start packet capture
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    tcpdump -i usb0 -w "/var/lib/vivisect/output/usb_capture_${TIMESTAMP}.pcap" -n &
    echo $! > /var/run/usb-capture.pid

    echo "[$(date)] Packet capture started (PID: $!)" >> "$LOGFILE"
fi

# Notify GUI if running
if pgrep -f "vivisect-gui" > /dev/null; then
    # Send signal to GUI (could use socket or file)
    touch /tmp/usb-connected
fi

exit 0
EOF

chmod +x /usr/local/bin/usb-gadget-connected

echo "✓ Created USB connection detection script"

echo "[5/6] Configuring DHCP server for USB interface..."

# Configure dnsmasq for USB interface
cat > /etc/dnsmasq.d/usb-gadget <<EOF
# USB Gadget DHCP Configuration
interface=usb0
dhcp-range=10.55.0.10,10.55.0.20,255.255.255.0,12h
dhcp-option=3,10.55.0.2
dhcp-option=6,8.8.8.8,8.8.4.4
EOF

# Restart dnsmasq
systemctl enable dnsmasq
systemctl restart dnsmasq || true

echo "✓ Configured DHCP server"

echo "[6/6] Setting up IP forwarding and NAT..."

# Enable IP forwarding
echo "net.ipv4.ip_forward=1" > /etc/sysctl.d/99-usb-gadget.conf
sysctl -p /etc/sysctl.d/99-usb-gadget.conf

# Set up iptables for NAT (if device has internet via wlan0/eth0)
iptables -t nat -A POSTROUTING -o wlan0 -j MASQUERADE 2>/dev/null || true
iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE 2>/dev/null || true
iptables -A FORWARD -i usb0 -j ACCEPT
iptables -A FORWARD -o usb0 -m state --state RELATED,ESTABLISHED -j ACCEPT

# Save iptables rules
if command -v netfilter-persistent &> /dev/null; then
    netfilter-persistent save
fi

echo "✓ Configured IP forwarding and NAT"

echo ""
echo "================================================================"
echo "  USB Gadget Mode Setup Complete!"
echo "================================================================"
echo ""
echo "Configuration:"
echo "  Device IP: 10.55.0.2"
echo "  Host IP:   10.55.0.1"
echo "  Interface: usb0"
echo ""
echo "What happens when you plug into a PC:"
echo "  1. PC detects USB Ethernet adapter"
echo "  2. PC gets IP address via DHCP (10.55.0.10-20)"
echo "  3. Vivisect automatically starts packet capture"
echo "  4. Network traffic is logged to /var/lib/vivisect/output/"
echo ""
echo "IMPORTANT: You must REBOOT for changes to take effect!"
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
