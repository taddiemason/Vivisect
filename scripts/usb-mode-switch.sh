#!/bin/bash
# USB Gadget Mode Switcher for Vivisect
# Switch between multi-function, mass-storage-only, and network-only modes

set -e

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Error: This script must be run as root (use sudo)"
    exit 1
fi

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

STORAGE_FILE="/var/lib/vivisect/usb_storage.img"

show_current_mode() {
    echo -e "${BLUE}Current USB Gadget Mode:${NC}"

    if lsmod | grep -q "g_multi"; then
        echo -e "${GREEN}✓ Multi-Function Mode${NC} (Network + Mass Storage + Serial)"
    elif lsmod | grep -q "g_mass_storage"; then
        echo -e "${GREEN}✓ Mass Storage Only Mode${NC} (USB Flash Drive)"
    elif lsmod | grep -q "g_ether"; then
        echo -e "${GREEN}✓ Network Only Mode${NC} (USB Ethernet)"
    else
        echo -e "${YELLOW}⚠ No USB Gadget Module Loaded${NC}"
    fi
    echo ""
}

unload_all_gadgets() {
    echo "Unloading existing USB gadget modules..."
    modprobe -r g_multi 2>/dev/null || true
    modprobe -r g_ether 2>/dev/null || true
    modprobe -r g_serial 2>/dev/null || true
    modprobe -r g_mass_storage 2>/dev/null || true
    sleep 1
    echo "✓ Unloaded"
}

switch_to_multi() {
    echo -e "${BLUE}Switching to Multi-Function Mode...${NC}"
    unload_all_gadgets

    if [ ! -f "$STORAGE_FILE" ]; then
        echo "Error: Mass storage backing file not found: $STORAGE_FILE"
        echo "Run setup-usb-gadget.sh first"
        exit 1
    fi

    modprobe g_multi \
        file="$STORAGE_FILE" \
        removable=1 \
        ro=0 \
        stall=0 \
        iSerialNumber=VIVISECT001 \
        iManufacturer="Vivisect" \
        iProduct="Forensics Suite"

    sleep 2

    # Configure network
    if ip link show usb0 &>/dev/null; then
        ip link set usb0 up
        ip addr add 10.55.0.2/24 dev usb0 2>/dev/null || true
    fi

    echo -e "${GREEN}✓ Multi-Function Mode Active${NC}"
    echo "  Functions: Network + Mass Storage + Serial Console"
    echo "  Network: usb0 (10.55.0.2)"
    echo "  Storage: $STORAGE_FILE"
    echo "  Serial: /dev/ttyGS0"
}

switch_to_mass_storage() {
    local READ_ONLY=${1:-0}

    if [ "$READ_ONLY" = "1" ]; then
        echo -e "${BLUE}Switching to Mass Storage Only Mode (Read-Only)...${NC}"
    else
        echo -e "${BLUE}Switching to Mass Storage Only Mode (Read-Write)...${NC}"
    fi

    unload_all_gadgets

    if [ ! -f "$STORAGE_FILE" ]; then
        echo "Error: Mass storage backing file not found: $STORAGE_FILE"
        echo "Run setup-usb-gadget.sh first"
        exit 1
    fi

    modprobe g_mass_storage \
        file="$STORAGE_FILE" \
        removable=1 \
        ro=$READ_ONLY \
        stall=0 \
        iSerialNumber=VIVISECT001 \
        iManufacturer="Vivisect" \
        iProduct="Forensics Evidence Drive"

    sleep 2

    echo -e "${GREEN}✓ Mass Storage Only Mode Active${NC}"
    echo "  Device appears as: USB Flash Drive"
    echo "  Label: VIVISECT"
    echo "  Size: $(du -h "$STORAGE_FILE" | cut -f1)"
    if [ "$READ_ONLY" = "1" ]; then
        echo "  Mode: Read-Only (forensically sound)"
    else
        echo "  Mode: Read-Write"
    fi
    echo ""
    echo "  Host PC will see:"
    echo "    Windows: Drive letter (E:, F:, etc.)"
    echo "    Linux:   /dev/sdb1 or similar"
    echo "    Mac:     /Volumes/VIVISECT"
}

switch_to_network() {
    echo -e "${BLUE}Switching to Network Only Mode...${NC}"
    unload_all_gadgets

    modprobe g_ether \
        iSerialNumber=VIVISECT001 \
        iManufacturer="Vivisect" \
        iProduct="Forensics Network Adapter"

    sleep 2

    # Configure network
    if ip link show usb0 &>/dev/null; then
        ip link set usb0 up
        ip addr add 10.55.0.2/24 dev usb0 2>/dev/null || true
    fi

    echo -e "${GREEN}✓ Network Only Mode Active${NC}"
    echo "  Device appears as: USB Ethernet Adapter"
    echo "  Interface: usb0"
    echo "  Device IP: 10.55.0.2"
    echo "  Host IP: 10.55.0.1"
}

show_usage() {
    cat << EOF
${BLUE}Vivisect USB Gadget Mode Switcher${NC}

Usage: sudo $0 [MODE] [OPTIONS]

Modes:
  multi          Multi-function mode (Network + Storage + Serial)
  storage        Mass storage only (USB flash drive, read-write)
  storage-ro     Mass storage only (read-only for forensics)
  network        Network only (USB Ethernet)
  status         Show current mode

Examples:
  sudo $0 multi              # Switch to multi-function mode
  sudo $0 storage            # Switch to USB flash drive (read-write)
  sudo $0 storage-ro         # Switch to USB flash drive (read-only)
  sudo $0 network            # Switch to USB Ethernet only
  sudo $0 status             # Show current mode

Current Mode:
EOF
    show_current_mode
}

# Main
case "${1:-status}" in
    multi)
        switch_to_multi
        ;;
    storage)
        switch_to_mass_storage 0
        ;;
    storage-ro)
        switch_to_mass_storage 1
        ;;
    network)
        switch_to_network
        ;;
    status)
        show_current_mode
        ;;
    -h|--help|help)
        show_usage
        ;;
    *)
        echo -e "${RED}Error: Unknown mode '$1'${NC}"
        echo ""
        show_usage
        exit 1
        ;;
esac
