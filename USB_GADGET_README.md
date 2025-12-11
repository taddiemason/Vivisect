# Vivisect USB Gadget Mode

## Overview

USB Gadget Mode allows your Vivisect device (especially Raspberry Pi Zero/4) to act as a **USB peripheral** that plugs directly into a target PC. When connected, it appears as a USB Ethernet adapter and automatically captures network traffic and performs forensics collection.

## 🎯 What It Does

```
┌─────────────────────────┐
│   Target PC             │
│                         │
│   USB Port ──────────┐  │
└───────────────────────┼──┘
                        │ USB Cable
                        │
                   ┌────▼────────────────────┐
                   │  Vivisect Device        │
                   │  (Raspberry Pi Zero)    │
                   │                         │
                   │  ✅ Appears as USB Eth │
                   │  ✅ Captures traffic    │
                   │  ✅ Auto-collects data  │
                   │  ✅ Logs everything     │
                   └─────────────────────────┘
```

### When You Plug In:

1. **PC detects "USB Ethernet Adapter"**
2. **PC gets IP address** (10.55.0.10-20)
3. **Vivisect starts packet capture** automatically
4. **All network traffic** is logged
5. **Forensics collection** begins
6. **GUI shows "Connected to Host PC"**

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
- Configure boot files (`config.txt`, `cmdline.txt`)
- Set up USB Ethernet (`usb0` interface)
- Configure DHCP server
- Enable IP forwarding and NAT
- Install monitoring service
- Set up auto-capture

**IMPORTANT: You MUST reboot after installation!**

```bash
sudo reboot
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
