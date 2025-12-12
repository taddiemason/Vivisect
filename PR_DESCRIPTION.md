# USB Gadget Mode Enhancements: Multi-Function, Mode Switching, and HID Keyboard

## Overview

This PR implements comprehensive USB gadget mode functionality for Vivisect, transforming the Raspberry Pi into a versatile forensics tool with multiple USB personalities. The device can now function as a network adapter, USB flash drive, serial console, and HID keyboard - either individually or simultaneously.

## Features Implemented

### 1. Multi-Function USB Gadget Mode (Priority 1)
**Provides three USB functions simultaneously:**
- ✅ **USB Ethernet** (Network forensics and remote access)
- ✅ **USB Mass Storage** (512MB FAT32 drive for reports/evidence)
- ✅ **USB Serial Console** (CLI access via /dev/ttyGS0)

**Implementation:**
- Updated setup-usb-gadget.sh to use g_multi kernel module
- Created 512MB FAT32 backing file at /var/lib/vivisect/usb_storage.img
- Automatic DHCP configuration (10.55.0.10-20 range)
- Auto-syncing reports to USB mass storage
- Connection detection and logging

### 2. Dynamic Mode Switching (Priority 2)
**Switch between USB modes without reboot:**
- 🔧 **Multi-Function** - All three functions enabled
- 💾 **Mass Storage (RW)** - USB flash drive with read-write access
- 🔒 **Mass Storage (RO)** - Forensically sound read-only mode
- 🌐 **Network Only** - USB Ethernet adapter

**Implementation:**
- CLI tool: scripts/usb-mode-switch.sh for quick switching
- Web GUI: Mode switching buttons with live status indicators
- Safe module unload/reload with automatic network reconfiguration
- Current mode detection and status reporting

### 3. HID Keyboard Mode (Priority 3)
**⚠️ SECURITY: Automated keystroke injection for authorized testing only**

**Features:**
- USB HID keyboard emulation via configfs
- Automated keystroke injection (BadUSB functionality)
- Pre-built forensics payloads (Windows/Linux triage)
- Custom string typing with configurable delays
- Full US keyboard layout support (65+ characters)

**Security Controls:**
- 🔴 Multiple authorization checkpoints in setup script
- 🔴 Explicit "yes" confirmation required
- 🔴 Syslog logging of all HID operations
- 🔴 Comprehensive legal warnings and disclaimers
- 🔴 Clear distinction between authorized/prohibited uses

### 4. HID Keyboard GUI (Latest Addition)
**Web interface for HID operations with prominent security warnings:**

**API Endpoints:**
- GET /api/usb/hid/status - Check HID device availability
- GET /api/usb/hid/payloads - List available payloads
- POST /api/usb/hid/send-string - Type custom text
- POST /api/usb/hid/execute-payload - Run pre-built scripts
- POST /api/usb/hid/mode/switch - Switch to HID mode

## Statistics

**Total Changes:**
- 15+ files modified/created
- 2,454+ lines of code added
- 4 new shell scripts
- 10+ new API endpoints

## Security Considerations

### HID Mode Restrictions
- ⚠️ **ONLY for authorized security testing and forensics**
- ⚠️ Requires explicit written permission
- ⚠️ All operations logged for accountability
- ⚠️ Unauthorized use may be illegal

---

**By merging this PR, Vivisect gains comprehensive USB gadget capabilities with strong security controls for authorized security testing and digital forensics operations.**
