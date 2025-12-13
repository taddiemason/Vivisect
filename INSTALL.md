# Vivisect Installation Guide

This guide provides multiple installation options for Vivisect, depending on your system and requirements.

## Quick Start (Recommended)

If you're encountering package availability issues, use the **minimal installation**:

```bash
cd Vivisect
sudo chmod +x scripts/install-minimal.sh
sudo ./scripts/install-minimal.sh
```

This installs only the core dependencies that are commonly available across all Debian-based distributions.

## Installation Options

### Option 1: Minimal Installation (Recommended for Most Users)

**Best for:** Users who want a working installation without optional tools, or those experiencing package availability issues.

```bash
sudo ./scripts/install-minimal.sh
```

**What it installs:**
- Core Python dependencies (Flask, Scapy, etc.)
- Essential system tools (tcpdump, tshark, libmagic)
- Vivisect application files
- Web GUI support

**What it skips:**
- Optional forensics tools that may not be available
- GUI kiosk mode dependencies
- Advanced tools like Volatility, autopsy, etc.

### Option 2: Full Installation

**Best for:** Forensics professionals who want all available tools.

```bash
sudo ./scripts/install.sh
```

**What it installs:**
- Everything from minimal installation
- Optional forensics tools (if available):
  - foremost, scalpel, dcfldd
  - sleuthkit, binwalk, exiftool
  - autopsy, guymager, bulk-extractor
  - yara, clamav, chkrootkit
- GUI kiosk mode support

**Note:** This script will continue even if some packages are unavailable, showing warnings instead of failing.

### Option 3: Manual Installation

**Best for:** Advanced users who want full control.

```bash
# 1. Install core dependencies
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-dev \
    tcpdump tshark libmagic1 libmagic-dev git build-essential

# 2. Install Python packages
pip3 install --upgrade pip
pip3 install -r requirements.txt

# 3. Create directories
sudo mkdir -p /opt/vivisect
sudo mkdir -p /var/lib/vivisect/output
sudo mkdir -p /var/log/vivisect

# 4. Copy files
sudo cp -r src /opt/vivisect/
sudo cp requirements.txt /opt/vivisect/

# 5. Create symlinks (optional)
sudo ln -sf /opt/vivisect/src/main.py /usr/local/bin/vivisect
sudo ln -sf /opt/vivisect/src/web/run_server.py /usr/local/bin/vivisect-gui
sudo chmod +x /usr/local/bin/vivisect /usr/local/bin/vivisect-gui
```

## Testing Your Installation

After installation, test that Vivisect is working:

### 1. Test Enhanced Reporting

```bash
cd /opt/vivisect
python3 examples/demo_enhanced_reports.py
```

This will generate sample forensics reports with visualizations in `./demo_output/`.

### 2. Start the Web GUI

```bash
cd /opt/vivisect
python3 src/web/run_server.py
```

Then open your browser to: http://localhost:5000

### 3. Check Installed Components

```bash
# Check Python dependencies
pip3 list | grep -E "(Flask|scapy|python-magic)"

# Check system tools
which tcpdump tshark

# Check Vivisect installation
ls -l /opt/vivisect/
```

## Troubleshooting Common Issues

### Issue: "Package 'X' has no installation candidate"

**Solution:** Use the minimal installation script, which skips unavailable packages:
```bash
sudo ./scripts/install-minimal.sh
```

### Issue: Python package installation fails

**Solution:** Update pip and try again:
```bash
sudo pip3 install --upgrade pip
sudo pip3 install -r requirements.txt --no-cache-dir
```

### Issue: Permission denied errors

**Solution:** Ensure you're running with sudo:
```bash
sudo ./scripts/install-minimal.sh
```

### Issue: Missing system dependencies on older systems

**Solution:** Some packages may have different names. Try:
```bash
# For older Ubuntu/Debian
sudo apt-get install -y python3-scapy python3-flask

# For newer systems, pip install should work
pip3 install scapy flask
```

## Package Availability by Distribution

| Package | Ubuntu 20.04+ | Debian 11+ | Kali Linux | Notes |
|---------|--------------|-----------|------------|-------|
| tcpdump | ✅ | ✅ | ✅ | Always available |
| tshark | ✅ | ✅ | ✅ | Always available |
| foremost | ✅ | ✅ | ✅ | Usually available |
| dcfldd | ⚠️ | ⚠️ | ✅ | May need universe repo |
| sleuthkit | ✅ | ✅ | ✅ | Usually available |
| volatility | ❌ | ❌ | ✅ | Use pip3 install volatility3 |
| autopsy | ⚠️ | ⚠️ | ✅ | May need PPA/backports |
| bulk-extractor | ⚠️ | ⚠️ | ✅ | Limited availability |

**Legend:**
- ✅ Available in standard repos
- ⚠️ May require additional repos or have limited availability
- ❌ Not in standard repos (use alternative method)

## Enabling Additional Repositories

If you need packages that aren't available, try:

### Ubuntu
```bash
sudo add-apt-repository universe
sudo apt-get update
```

### Debian
```bash
# Enable backports
echo "deb http://deb.debian.org/debian bullseye-backports main" | sudo tee -a /etc/apt/sources.list
sudo apt-get update
```

## Post-Installation Configuration

### Set Output Directory Permissions

```bash
sudo chown -R $USER:$USER /var/lib/vivisect/output
sudo chmod -R 755 /var/lib/vivisect/output
```

### Configure Web GUI Port

Edit `/etc/vivisect/vivisect.conf` and set:
```json
{
    "web_port": 5000,
    "web_host": "0.0.0.0"
}
```

## Next Steps

1. **Try the demo:** `python3 /opt/vivisect/examples/demo_enhanced_reports.py`
2. **Read the README:** `cat /opt/vivisect/README.md`
3. **Start the web GUI:** `vivisect-gui` or `python3 /opt/vivisect/src/web/run_server.py`
4. **View example reports:** Open the generated HTML reports in `demo_output/`

## Getting Help

If you continue to experience installation issues:

1. Check which packages failed to install
2. Try the minimal installation script
3. Manually install only the Python dependencies: `pip3 install -r requirements.txt`
4. Report issues at: https://github.com/taddiemason/Vivisect/issues

Include:
- Your OS version: `lsb_release -a`
- Python version: `python3 --version`
- Error messages from installation
