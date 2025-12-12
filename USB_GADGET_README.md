# Vivisect USB Gadget Mode

## Overview

USB Gadget Mode allows your Vivisect device (especially Raspberry Pi Zero/4) to act as a **USB peripheral** that plugs directly into a target PC. Using **Multi-Function Gadget Mode (g_multi)**, it presents three simultaneous USB devices to the host:

1. **USB Ethernet** - Network interface for traffic capture
2. **USB Mass Storage** - Drive for accessing reports/evidence
3. **USB Serial Console** - Terminal access for CLI control

## 🎯 What It Does

```
┌─────────────────────────────────────────┐
│   Target PC                             │
│                                         │
│   USB Port ──────────────────────────┐  │
└───────────────────────────────────────┼──┘
                                        │ USB Cable
                                        │
                   ┌────────────────────▼─────────────────────┐
                   │  Vivisect Device (Raspberry Pi Zero)     │
                   │                                          │
                   │  ✅ USB Ethernet Adapter (usb0)         │
                   │     - Captures network traffic          │
                   │     - IP: 10.55.0.2                     │
                   │                                          │
                   │  💾 USB Mass Storage (512MB)            │
                   │     - Reports & evidence access         │
                   │     - Auto-synced                       │
                   │                                          │
                   │  ⌨️  USB Serial Console (/dev/ttyGS0)   │
                   │     - CLI access (115200 baud)          │
                   │     - Remote control                    │
                   └──────────────────────────────────────────┘
```

### When You Plug In:

1. **PC detects THREE USB devices:**
   - USB Ethernet Adapter (network interface)
   - USB Mass Storage Drive ("VIVISECT" 512MB)
   - USB Serial Console (COM port)
2. **Network configured automatically** (PC gets IP 10.55.0.10-20)
3. **Packet capture starts** on USB network interface
4. **Mass storage** shows reports and evidence
5. **Serial console** provides CLI access (screen/PuTTY)
6. **GUI shows "Connected to Host PC"** with function status

---

## 🔧 Installation

### Prerequisites

- **Raspberry Pi Zero W** (recommended) or Pi 4
- **Debian/Raspbian OS**
- **Vivisect** already installed
- **USB cable** (Data capable, not charge-only!)

### Install USB Gadget Mode

```bash
cd /path/to/Vivisect
sudo ./scripts/setup-usb-gadget.sh
```

The script will:
- Configure boot files (`config.txt`, `cmdline.txt`) for dwc2 driver
- Set up **g_multi** kernel module for multi-function mode
- Create 512MB mass storage backing file (FAT32)
- Configure USB Ethernet (`usb0` interface)
- Configure DHCP server (10.55.0.10-20 range)
- Enable IP forwarding and NAT
- Install monitoring service
- Set up auto-capture and sync scripts

**IMPORTANT: You MUST reboot after installation!**

```bash
sudo reboot
```

After reboot, verify all functions are active:
```bash
# Check loaded modules
lsmod | grep g_multi

# Check network interface
ip addr show usb0

# Check mass storage
ls -lh /var/lib/vivisect/usb_storage.img

# Check serial device
ls -l /dev/ttyGS0
```

---

## 🚀 Usage

### Quick Start

**1. Install USB Gadget Mode** (one-time setup)
```bash
sudo ./scripts/setup-usb-gadget.sh
sudo reboot
```

**2. Plug Into Target PC**
```bash
# Connect Vivisect device to target PC's USB port
# Use data cable (not charge-only)
```

**3. Wait 10-20 Seconds**
- Target PC detects USB Ethernet
- Vivisect auto-configures
- Packet capture starts

**4. Check GUI**
- Dashboard shows: ✅ Connected to Host PC
- Automatic collection begins
- Traffic logged to `/var/lib/vivisect/output/`

### Manual Control

**Check USB Status:**
```bash
# Via CLI
ip link show usb0

# Check if connected
ping 10.55.0.1
```

**View Captured Traffic:**
```bash
ls -lh /var/lib/vivisect/output/usb_capture_*
```

**Monitor Connection Log:**
```bash
tail -f /var/log/vivisect/usb-gadget.log
```

**Stop Packet Capture:**
```bash
# Find process
pgrep tcpdump

# Stop it
sudo kill $(cat /var/run/usb-capture.pid)
```

---

## 🔧 Multi-Function Features

### USB Mass Storage

The device presents a 512MB FAT32 USB drive to the host PC containing forensics reports and evidence.

**On Host PC (Windows):**
- Drive appears as "VIVISECT (E:)" or similar
- Browse reports and evidence directly
- Read-only for forensics integrity (configurable)

**On Host PC (Linux/Mac):**
```bash
# Drive auto-mounts to /media/VIVISECT or similar
ls /media/VIVISECT/

# Manual mount if needed
sudo mount /dev/sdb1 /mnt/vivisect
```

**Sync Reports to USB Storage:**
```bash
# On Vivisect device
sudo /home/user/Vivisect/scripts/usb-storage-sync.sh

# This copies:
# - /var/lib/vivisect/output/reports → USB:/reports/
# - /var/lib/vivisect/output/evidence → USB:/evidence/
# - Recent logs → USB:/logs/
```

**Auto-Sync:**
Reports are automatically synced to USB storage when:
- New reports are generated
- USB connection is established
- Manual sync is triggered via GUI

### USB Serial Console

Access the Vivisect CLI directly via USB serial connection (no network needed).

**On Host PC (Linux/Mac):**
```bash
# Find serial device
ls /dev/ttyACM*

# Connect with screen (115200 baud)
screen /dev/ttyACM0 115200

# Or with minicom
sudo minicom -D /dev/ttyACM0 -b 115200

# Exit screen: Ctrl+A then K
```

**On Host PC (Windows):**
1. Device Manager → Ports (COM & LPT)
2. Find "USB Serial Device (COM3)" or similar
3. Use PuTTY:
   - Connection type: Serial
   - Serial line: COM3
   - Speed: 115200

**Serial Console Usage:**
```bash
# Login (if prompted)
# Then use Vivisect CLI

vivisect disk --list
vivisect network --capture-live eth0
vivisect collect --all
```

**Enable Getty on Serial (if needed):**
```bash
# On Vivisect device
sudo systemctl enable serial-getty@ttyGS0.service
sudo systemctl start serial-getty@ttyGS0.service
```

### Combining All Three Functions

Example workflow using all USB functions simultaneously:

1. **Network (usb0):** Captures target PC's network traffic
2. **Mass Storage:** Access captured reports without SSH/network config
3. **Serial Console:** Control Vivisect and trigger collection

```bash
# On Host PC via serial console (screen /dev/ttyACM0 115200):
vivisect network --capture-live usb0 --duration 300

# While that runs, on Host PC:
# - Check network: ping 10.55.0.2
# - View live reports: ls /media/VIVISECT/reports/
# - Monitor traffic in real-time

# All simultaneously!
```

---

## 🔄 Mode Switching

Vivisect supports switching between different USB gadget modes without rebooting. Choose the mode that best fits your workflow.

### Available Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| **Multi-Function** | Network + Storage + Serial | Full forensics suite, maximum flexibility |
| **Mass Storage (RW)** | USB flash drive (read-write) | Quick evidence handoff, report sharing |
| **Mass Storage (RO)** | USB flash drive (read-only) | Forensically sound evidence presentation |
| **Network Only** | USB Ethernet adapter | Network traffic capture only |

### Switch Via Command Line

Use the `usb-mode-switch.sh` script:

```bash
# Show current mode
sudo /path/to/Vivisect/scripts/usb-mode-switch.sh status

# Switch to multi-function mode (default)
sudo /path/to/Vivisect/scripts/usb-mode-switch.sh multi

# Switch to USB flash drive (read-write)
sudo /path/to/Vivisect/scripts/usb-mode-switch.sh storage

# Switch to USB flash drive (read-only for forensics)
sudo /path/to/Vivisect/scripts/usb-mode-switch.sh storage-ro

# Switch to network only
sudo /path/to/Vivisect/scripts/usb-mode-switch.sh network
```

### Switch Via Web GUI

1. Open Vivisect GUI in browser
2. Navigate to **Dashboard**
3. Find **USB Gadget Mode** card
4. Click desired mode button:
   - **🔧 Multi-Function** - All three functions
   - **💾 USB Drive (RW)** - Flash drive read-write
   - **🔒 USB Drive (RO)** - Flash drive read-only
   - **🌐 Network Only** - USB Ethernet

Mode switches take 2-5 seconds. The host PC will see a brief disconnect/reconnect.

### Mass Storage Only Mode

**Best for:**
- Quick evidence handoff to another investigator
- Presenting reports to non-technical users
- Universal compatibility (works on any OS)
- No network configuration needed

**Read-Write Mode:**
```bash
sudo ./scripts/usb-mode-switch.sh storage
```
- Host PC can read AND write to the drive
- Useful for collecting additional evidence
- Drive labeled "VIVISECT"

**Read-Only Mode (Recommended for evidence):**
```bash
sudo ./scripts/usb-mode-switch.sh storage-ro
```
- Host PC can ONLY read from the drive
- Preserves forensic integrity
- Prevents accidental modification
- Write-blocker functionality

**Sync Reports Before Switching:**
```bash
# Sync latest reports to USB storage
sudo ./scripts/usb-storage-sync.sh

# Then switch to mass storage only
sudo ./scripts/usb-mode-switch.sh storage-ro
```

**On Host PC:**

Windows:
- Drive appears as new drive letter (E:, F:, etc.)
- Browse normally via File Explorer
- Reports in `E:\reports\`
- Evidence in `E:\evidence\`

Linux:
- Auto-mounts to `/media/VIVISECT/`
- Or manually: `sudo mount /dev/sdb1 /mnt`

Mac:
- Auto-mounts to `/Volumes/VIVISECT/`
- Appears in Finder

### When to Use Each Mode

**Multi-Function Mode:**
- Active forensics collection
- Need all capabilities simultaneously
- Advanced users with proper drivers

**Mass Storage (Read-Only):**
- Evidence handoff
- Court proceedings
- Forensically sound presentation
- Prevent tampering

**Mass Storage (Read-Write):**
- Collecting files from host PC
- Collaborative investigation
- Adding external evidence

**Network Only:**
- Pure traffic capture
- Minimal footprint
- Host PC only sees network adapter

---

## 📊 Configuration

### Network Configuration

**Default IP Addresses:**
- **Vivisect Device:** 10.55.0.2
- **Target PC:** 10.55.0.1 (gateway)
- **DHCP Range:** 10.55.0.10 - 10.55.0.20

**To change IPs**, edit `/etc/network/interfaces.d/usb0`:
```bash
sudo nano /etc/network/interfaces.d/usb0
```

### Auto-Collection Settings

**Enable/Disable Auto-Collection:**

Edit `/etc/vivisect/vivisect.conf`:
```json
{
  "usb_auto_collect": true,  // Set to false to disable
  "modules": {
    "usb_gadget": {
      "enabled": true,
      "auto_capture": true,
      "auto_analyze": true
    }
  }
}
```

---

## 🔍 What Gets Captured

### Automatically Collected Data

When you plug into a target PC:

✅ **Network Traffic**
- All TCP/IP packets on `usb0`
- HTTP/HTTPS connections
- DNS queries
- ARP table

✅ **Host Information**
- Host MAC address
- IP address
- Network connections
- Open ports (if scanning enabled)

✅ **Timeline**
- Connection timestamp
- Traffic volume
- Disconnection time

### Output Files

Located in `/var/lib/vivisect/output/`:

```
USB_20241211_143022_capture.pcap  - Packet capture
USB_20241211_143022_report.json   - Forensics report
USB_20241211_143022_report.html   - HTML report
```

---

## 💡 Use Cases

### 1. Network Traffic Monitoring

```
Scenario: Monitor all network activity from suspect PC

1. Plug Vivisect into target PC's USB port
2. Device appears as network adapter
3. All traffic routes through Vivisect
4. Capture stored for analysis
```

### 2. Stealth Forensics Collection

```
Scenario: Covert evidence collection

1. Device appears as innocent USB Ethernet adapter
2. No software installation required on target
3. Automatic background capture
4. Target user may not notice
```

### 3. Incident Response

```
Scenario: Quick evidence collection during incident

1. Plug into compromised system
2. Immediate traffic capture starts
3. No target system modification
4. Evidence preserved forensically
```

### 4. Network Analysis

```
Scenario: Analyze what a PC is communicating with

1. Connect Vivisect between PC and network
2. Capture all communications
3. Analyze protocols, domains, IPs
4. Detect C2, exfiltration, malware communication
```

---

## 🛠️ Troubleshooting

### Device Not Detected by Host PC

**Check USB Cable:**
```bash
# Must be data cable, not charge-only
# Try different cable
```

**Verify Kernel Modules:**
```bash
lsmod | grep dwc2
lsmod | grep g_ether

# Should see both modules loaded
```

**Check Boot Configuration:**
```bash
cat /boot/config.txt | grep dwc2
# Should show: dtoverlay=dwc2

cat /boot/cmdline.txt | grep modules-load
# Should show: modules-load=dwc2,g_ether
```

**Reboot:**
```bash
sudo reboot
```

### No Network Connection

**Check Interface:**
```bash
ip link show usb0
# Should show "state UP"
```

**Bring Up Manually:**
```bash
sudo ip link set usb0 up
sudo ip addr add 10.55.0.2/24 dev usb0
```

**Check DHCP Server:**
```bash
sudo systemctl status dnsmasq
sudo systemctl restart dnsmasq
```

### Host PC Can't Get IP Address

**Check DHCP Configuration:**
```bash
cat /etc/dnsmasq.d/usb-gadget

# Should show:
# interface=usb0
# dhcp-range=10.55.0.10,10.55.0.20,255.255.255.0,12h
```

**Manually Set IP on Host PC:**
- IP Address: 10.55.0.10
- Subnet Mask: 255.255.255.0
- Gateway: 10.55.0.2

### Capture Not Starting

**Check Monitor Service:**
```bash
sudo systemctl status usb-gadget-monitor
sudo systemctl restart usb-gadget-monitor
```

**View Logs:**
```bash
tail -f /var/log/vivisect/usb-monitor.log
```

**Start Capture Manually:**
```bash
sudo tcpdump -i usb0 -w /tmp/test-capture.pcap
```

---

## 🔒 Security Considerations

### Authorized Use Only

⚠️ **WARNING**: USB Gadget Mode is designed for:
- Authorized penetration testing
- Legal forensics investigations
- Security research with permission
- Incident response on owned systems

**Illegal uses:**
- ❌ Unauthorized surveillance
- ❌ Corporate espionage
- ❌ Privacy violations
- ❌ Unauthorized network monitoring

### Detection Considerations

**Host PC will see:**
- New USB Ethernet adapter appeared
- New network interface
- DHCP requests
- May appear in device logs

**To minimize detection:**
- Use during authorized maintenance
- Label device appropriately
- Ensure proper authorization
- Document in incident response plan

### Data Protection

**Captured traffic contains:**
- Potentially sensitive information
- Credentials (if unencrypted)
- Personal data
- Business communications

**Protect captured data:**
```bash
# Encrypt output directory
sudo cryptsetup luksFormat /dev/sdb1
sudo cryptsetup open /dev/sdb1 evidence
sudo mount /dev/mapper/evidence /var/lib/vivisect/output

# Set proper permissions
sudo chmod 700 /var/lib/vivisect/output
```

---

## 🎛️ Advanced Features

### Man-in-the-Middle Mode

**Enable traffic interception:**

```python
# Via Python API
from modules import USBGadget
usb = USBGadget(logger, config)
usb.enable_mitm_mode()
```

**What it does:**
- Intercepts HTTP traffic (port 80)
- Redirects to local proxy (port 8080)
- Can inspect/modify traffic
- Logs all requests

### Network Sharing

**Give target PC internet via Vivisect:**

Already enabled by default! The device will:
- NAT traffic from `usb0` to `wlan0`/`eth0`
- Provide internet to target PC
- Route all traffic through Vivisect
- Log everything that passes through

### Custom Scripts on Connection

**Run custom script when PC connects:**

Edit `/usr/local/bin/usb-gadget-connected`:
```bash
#!/bin/bash
# Your custom actions here

# Example: Send notification
curl -X POST https://your-server.com/api/alert \
  -d "status=usb_connected&device=$HOSTNAME"

# Example: Run specific collection
/usr/local/bin/vivisect artifact browser
```

---

## 📈 Performance

### Raspberry Pi Zero W

- **Throughput:** ~80 Mbps
- **Suitable for:** Most scenarios
- **Size:** Perfect for covert deployment
- **Power:** Can run on PC's USB power

### Raspberry Pi 4

- **Throughput:** ~300+ Mbps
- **Suitable for:** High-bandwidth scenarios
- **Size:** Larger, less covert
- **Power:** May need external power

---

## 📝 Example Scenarios

### Scenario 1: Malware C2 Detection

```bash
# 1. Plug Vivisect into suspect PC
# 2. Let it run for 1 hour
# 3. Analyze captured traffic

# View captured data
cd /var/lib/vivisect/output
ls -lh USB_*

# Analyze with tshark
tshark -r USB_20241211_140000_capture.pcap \
  -Y "http or dns" \
  -T fields -e ip.dst -e dns.qry.name

# Look for suspicious domains/IPs
```

### Scenario 2: Data Exfiltration Detection

```bash
# 1. Connect during business hours
# 2. Monitor for large outbound transfers

# Find large transfers
tshark -r capture.pcap -q -z io,phs

# Extract file transfers
tshark -r capture.pcap --export-objects http,./extracted
```

### Scenario 3: Quick Network Baseline

```bash
# 1. Connect to PC for 10 minutes
# 2. Establish normal traffic baseline
# 3. Compare with suspicious behavior later

# Save baseline
cp USB_baseline_capture.pcap /evidence/baselines/
```

---

## 🔄 Updates & Maintenance

### Update USB Gadget Configuration

```bash
# Re-run setup script
sudo ./scripts/setup-usb-gadget.sh

# Or update manually
sudo nano /etc/network/interfaces.d/usb0
sudo nano /etc/dnsmasq.d/usb-gadget
```

### Monitor Service Updates

```bash
# Update monitor script
sudo nano /usr/local/bin/usb-gadget-monitor

# Restart service
sudo systemctl restart usb-gadget-monitor
```

---

## 🆘 Support

### Getting Help

**Check Status:**
```bash
# System status
systemctl status usb-gadget-monitor

# Interface status
ip addr show usb0

# Recent logs
journalctl -u usb-gadget-monitor -n 50
```

**Common Issues:**
1. Device not detected → Check cable and boot config
2. No IP on host → Check dnsmasq service
3. No capture starting → Check monitor service
4. Slow performance → Check CPU usage

### Debug Mode

**Enable verbose logging:**
```bash
# Edit monitor script
sudo nano /usr/local/bin/usb-gadget-monitor

# Add at top:
set -x  # Enable debug output

# Restart
sudo systemctl restart usb-gadget-monitor

# View debug output
journalctl -u usb-gadget-monitor -f
```

---

## 📚 Additional Resources

- **Main Documentation:** [README.md](README.md)
- **GUI Guide:** [GUI_README.md](GUI_README.md)
- **Quick Start:** [QUICKSTART.md](QUICKSTART.md)

---

## ⚖️ Legal & Ethical Use

**Remember:**
- Always obtain proper authorization
- Document your authorization
- Respect privacy laws
- Follow chain of custody procedures
- Ensure compliance with regulations
- Use for legitimate purposes only

**This tool is for authorized security professionals, forensics investigators, and researchers only.**

---

**USB Gadget Mode transforms your Vivisect device into a powerful network forensics tool that plugs directly into target systems!** 🔌
