# Vivisect - Digital Forensics Suite

**Vivisect** is a comprehensive, all-in-one digital forensics suite designed for Debian-based Linux systems. It provides a unified platform for disk imaging, file analysis, network forensics, memory analysis, and artifact extraction.

## Features

### 🔍 Disk Imaging
- Create forensic images using `dd` or `dcfldd`
- Built-in hash verification (MD5, SHA-1, SHA-256)
- Support for image splitting and compression
- Device information gathering

### 📁 File Analysis
- Multi-algorithm hash calculation
- File carving and recovery
- Metadata extraction
- Entropy analysis (detect encryption/compression)
- String extraction
- Hidden data detection

### 🌐 Network Forensics
- Live packet capture
- PCAP file analysis
- Protocol hierarchy analysis
- Suspicious traffic detection
- File extraction from network captures
- DNS query analysis
- C2 traffic detection

### 💾 Memory Analysis
- Memory dump creation (LiME, AVML, dd)
- Volatility-based analysis
- Process enumeration
- Network connection extraction
- Malware scanning
- Live system analysis

### 🗃️ Artifact Extraction
- Browser history (Chrome, Firefox, Edge)
- System logs (auth, syslog, kernel)
- User artifacts (bash history, SSH keys)
- Installed package enumeration
- Network configuration
- Persistence mechanism detection
- Timeline creation

## Installation

### Prerequisites
- Debian-based Linux distribution (Debian, Ubuntu, Kali Linux)
- Python 3.8 or higher
- Root/sudo access for installation

### Quick Install

```bash
# Clone the repository
git clone https://github.com/vivisect/vivisect.git
cd vivisect

# Make installation script executable
chmod +x scripts/install.sh

# Run installation (requires sudo)
sudo ./scripts/install.sh
```

The installation script will:
1. Install all required system dependencies
2. Install Python packages
3. Set up Vivisect in `/opt/vivisect`
4. Create configuration files
5. Install systemd service for auto-start on boot
6. Create command-line shortcuts

### Manual Installation

If you prefer manual installation:

```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install -y python3 python3-pip tcpdump tshark foremost \
    dcfldd sleuthkit libmagic1 volatility binwalk

# Install Python dependencies
pip3 install -r requirements.txt

# Copy files to /opt/vivisect
sudo mkdir -p /opt/vivisect
sudo cp -r src /opt/vivisect/

# Create symlink
sudo ln -s /opt/vivisect/src/main.py /usr/local/bin/vivisect
sudo chmod +x /usr/local/bin/vivisect
```

## Usage

### Command-Line Interface

Vivisect provides a comprehensive CLI with multiple subcommands:

```bash
vivisect <command> <subcommand> [options]
```

### Disk Imaging

**List available devices:**
```bash
vivisect disk list
```

**Create a disk image:**
```bash
vivisect disk image /dev/sdb evidence_disk.img --method dd
vivisect disk image /dev/sdb evidence_disk.img --method dcfldd --compress
```

**Verify disk image:**
```bash
vivisect disk verify evidence_disk.img --device /dev/sdb
```

### File Analysis

**Calculate file hashes:**
```bash
vivisect file hash /path/to/suspicious_file.exe
```

**Extract file metadata:**
```bash
vivisect file metadata /path/to/file.pdf
```

**Scan directory:**
```bash
vivisect file scan /home/user/Documents --recursive
```

**Carve files from image:**
```bash
vivisect file carve disk_image.dd --output ./carved_files
```

**Analyze file entropy:**
```bash
vivisect file entropy encrypted_file.bin
```

### Network Forensics

**List network interfaces:**
```bash
vivisect network list
```

**Capture network traffic:**
```bash
vivisect network capture eth0 capture.pcap --duration 300 --filter "port 80"
```

**Analyze PCAP file:**
```bash
vivisect network analyze capture.pcap
```

**Extract files from PCAP:**
```bash
vivisect network extract capture.pcap --output ./extracted
```

### Memory Analysis

**Create memory dump:**
```bash
vivisect memory dump --output memory.raw --method lime
```

**Analyze memory dump:**
```bash
vivisect memory analyze memory.raw --profile LinuxProfile
```

**Analyze running system:**
```bash
vivisect memory live
```

### Artifact Extraction

**Extract browser history:**
```bash
vivisect artifact browser --user /home/username
```

**Extract system logs:**
```bash
vivisect artifact logs --logdir /var/log
```

**Extract user artifacts:**
```bash
vivisect artifact user --user /home/username
```

**List installed packages:**
```bash
vivisect artifact packages
```

**Extract network configuration:**
```bash
vivisect artifact netconfig
```

**Find persistence mechanisms:**
```bash
vivisect artifact persistence
```

### Full Forensics Collection

Run a complete forensics collection for a case:

```bash
vivisect collect CASE-2024-001
```

Or specify specific modules:
```bash
vivisect collect CASE-2024-001 --modules memory artifacts network
```

This will:
- Analyze the running system
- Extract all available artifacts
- Generate comprehensive reports (JSON and HTML)
- Save everything to `/var/lib/vivisect/output`

### Generate Reports

```bash
vivisect report CASE-2024-001 --format html
vivisect report CASE-2024-001 --format json
vivisect report CASE-2024-001 --format txt
```

## Auto-Start Configuration

Vivisect can be configured to automatically start on system boot and perform initial forensics collection.

### Enable Auto-Start

```bash
sudo systemctl enable vivisect.service
sudo systemctl start vivisect.service
```

### Check Service Status

```bash
sudo systemctl status vivisect.service
```

### View Logs

```bash
sudo journalctl -u vivisect.service -f
```

### Manual Control

```bash
# Start the daemon
sudo vivisect-daemon start

# Stop the daemon
sudo vivisect-daemon stop

# Check status
sudo vivisect-daemon status

# Run collection
sudo vivisect-daemon collect
```

## Configuration

Configuration file location: `/etc/vivisect/vivisect.conf`

Example configuration:

```json
{
    "output_dir": "/var/lib/vivisect/output",
    "log_dir": "/var/log/vivisect",
    "temp_dir": "/tmp/vivisect",
    "auto_start": true,
    "modules": {
        "disk_imaging": {
            "enabled": true,
            "compression": true,
            "hash_algorithm": "sha256"
        },
        "file_analysis": {
            "enabled": true,
            "scan_depth": 10,
            "calculate_hashes": true
        },
        "network_forensics": {
            "enabled": true,
            "capture_interface": "eth0",
            "max_capture_size": "1GB"
        },
        "memory_analysis": {
            "enabled": true,
            "auto_dump": false
        },
        "artifact_extraction": {
            "enabled": true,
            "browser_artifacts": true,
            "system_logs": true
        }
    }
}
```

## Directory Structure

```
/opt/vivisect/              # Installation directory
├── src/
│   ├── core/               # Core framework
│   │   ├── config.py       # Configuration management
│   │   ├── logger.py       # Logging system
│   │   └── report.py       # Report generation
│   ├── modules/            # Forensics modules
│   │   ├── disk_imaging.py
│   │   ├── file_analysis.py
│   │   ├── network_forensics.py
│   │   ├── memory_analysis.py
│   │   └── artifact_extraction.py
│   ├── cli.py              # CLI interface
│   └── main.py             # Main entry point

/etc/vivisect/              # Configuration
└── vivisect.conf           # Main configuration file

/var/lib/vivisect/          # Data directory
└── output/                 # Forensics output

/var/log/vivisect/          # Log files
├── main.log
├── disk_imaging.log
├── file_analysis.log
├── network_forensics.log
├── memory_analysis.log
└── artifact_extraction.log
```

## Use Cases

### Incident Response
- Quickly analyze compromised systems
- Extract evidence for investigation
- Preserve volatile data

### Digital Forensics
- Create forensically sound disk images
- Analyze seized devices
- Generate court-ready reports

### Security Auditing
- Monitor network traffic
- Detect persistence mechanisms
- Analyze system artifacts

### Malware Analysis
- Extract suspicious files
- Analyze memory for malware
- Detect C2 communications

## Security Considerations

- **Run with appropriate permissions**: Many operations require root access
- **Forensic soundness**: Always verify image hashes
- **Chain of custody**: Use detailed logging and reporting
- **Data protection**: Secure storage of collected evidence
- **Legal compliance**: Ensure authorization before collection

## Troubleshooting

### Permission Denied Errors
```bash
# Ensure you're running with sudo for privileged operations
sudo vivisect <command>
```

### Missing Dependencies
```bash
# Reinstall dependencies
sudo apt-get install -f
pip3 install -r requirements.txt
```

### Service Won't Start
```bash
# Check service status
sudo systemctl status vivisect.service

# View detailed logs
sudo journalctl -u vivisect.service -n 50
```

### Python Module Not Found
```bash
# Ensure Python path is set correctly
export PYTHONPATH=/opt/vivisect/src:$PYTHONPATH
```

## Uninstallation

```bash
sudo ./scripts/uninstall.sh
```

This will:
1. Stop and disable the service
2. Remove Vivisect files
3. Optionally remove configuration and data

## Requirements

### System Requirements
- Debian-based Linux (Debian 10+, Ubuntu 20.04+, Kali Linux)
- Python 3.8 or higher
- At least 4GB RAM (8GB+ recommended for memory analysis)
- Sufficient disk space for evidence storage

### Software Dependencies
- tcpdump/tshark (network capture)
- foremost/scalpel (file carving)
- volatility (memory analysis)
- sleuthkit (file system analysis)
- dcfldd (enhanced disk imaging)

## Contributing

Contributions are welcome! Please ensure:
- Code follows PEP 8 style guidelines
- All modules include comprehensive error handling
- Logging is implemented for all operations
- Documentation is updated

## License

This project is intended for authorized security testing, digital forensics, incident response, and educational purposes only.

**IMPORTANT**: Always ensure you have proper authorization before performing forensics analysis on any system or network.

## Disclaimer

This tool is provided for legitimate digital forensics and incident response purposes. Users are responsible for ensuring they have proper authorization before analyzing any systems, networks, or data. The authors assume no liability for misuse of this software.

## Support

For issues, questions, or contributions:
- GitHub Issues: [Report a bug or request a feature]
- Documentation: See `/docs` directory for detailed guides

## Roadmap

- [ ] Windows artifact support (via Wine/mounted NTFS)
- [ ] Enhanced reporting with visualization
- [ ] REST API for remote operations
- [ ] Web-based GUI
- [ ] Plugin system for custom modules
- [ ] Cloud storage integration
- [ ] Automated threat intelligence lookup
- [ ] Timeline visualization

## Acknowledgments

Built with support from various open-source forensics tools and libraries:
- Volatility Framework
- The Sleuth Kit
- Scapy
- tcpdump/Wireshark project
- And many others in the digital forensics community