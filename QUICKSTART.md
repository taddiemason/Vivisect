# Vivisect Quick Start Guide

This guide will help you get Vivisect up and running quickly on your Debian system.

## Installation (5 minutes)

```bash
# 1. Clone the repository
git clone https://github.com/taddiemason/Vivisect.git
cd Vivisect

# 2. Run the installation script
sudo ./scripts/install.sh

# 3. Verify installation
vivisect --help
```

## First Run

### Option 1: Full Forensics Collection

Run a complete forensics collection on the current system:

```bash
sudo vivisect collect MY-FIRST-CASE
```

This will:
- Analyze running processes and memory
- Extract browser history
- Collect system logs
- Capture network configuration
- Generate reports in `/var/lib/vivisect/output`

### Option 2: Live System Analysis

Analyze the running system without creating disk images:

```bash
# Analyze memory
sudo vivisect memory live

# Extract browser artifacts
sudo vivisect artifact browser

# Check for persistence mechanisms
sudo vivisect artifact persistence
```

### Option 3: Analyze a Disk Image

If you have a disk image to analyze:

```bash
# Create a disk image
sudo vivisect disk image /dev/sdb evidence.img

# Carve files from the image
sudo vivisect file carve evidence.img

# Calculate hashes
sudo vivisect file hash evidence.img
```

## Common Use Cases

### Incident Response Scenario

```bash
# 1. Start with live analysis
sudo vivisect memory live

# 2. Capture current network traffic
sudo vivisect network capture eth0 incident.pcap --duration 300

# 3. Extract all artifacts
sudo vivisect artifact browser
sudo vivisect artifact logs
sudo vivisect artifact persistence

# 4. Generate comprehensive report
sudo vivisect collect INCIDENT-$(date +%Y%m%d)
```

### Network Analysis

```bash
# Capture traffic
sudo vivisect network capture eth0 capture.pcap --duration 60

# Analyze the capture
sudo vivisect network analyze capture.pcap

# Extract files from traffic
sudo vivisect network extract capture.pcap
```

### File Analysis

```bash
# Analyze a suspicious file
sudo vivisect file metadata /path/to/suspicious.exe
sudo vivisect file hash /path/to/suspicious.exe
sudo vivisect file entropy /path/to/suspicious.exe

# Scan a directory
sudo vivisect file scan /home/user/Downloads --recursive
```

## Auto-Start on Boot

Enable Vivisect to run automatically on system startup:

```bash
# Enable the service
sudo systemctl enable vivisect.service

# Start it now
sudo systemctl start vivisect.service

# Check status
sudo systemctl status vivisect.service
```

## View Results

All forensics data is stored in:
- **Output**: `/var/lib/vivisect/output/`
- **Logs**: `/var/log/vivisect/`

View the latest report:

```bash
ls -lt /var/lib/vivisect/output/ | head
```

Open HTML report in browser:

```bash
firefox /var/lib/vivisect/output/*_report.html
```

## Configuration

Edit the configuration file to customize behavior:

```bash
sudo nano /etc/vivisect/vivisect.conf
```

## Tips

1. **Always use sudo** - Most forensics operations require root privileges
2. **Check logs** - If something fails, check `/var/log/vivisect/`
3. **Verify hashes** - Always verify integrity with `vivisect disk verify`
4. **Document everything** - Use descriptive case IDs for organization

## Troubleshooting

### Command not found
```bash
# Ensure symlink exists
sudo ln -sf /opt/vivisect/src/main.py /usr/local/bin/vivisect
```

### Permission denied
```bash
# Run with sudo
sudo vivisect <command>
```

### Missing dependencies
```bash
# Reinstall
cd /path/to/Vivisect
sudo ./scripts/install.sh
```

## Next Steps

- Read the full documentation in `README.md`
- Explore all available commands: `vivisect --help`
- Configure auto-start: Edit `/etc/vivisect/vivisect.conf`
- Set up scheduled collections: Use cron or systemd timers

## Example Workflow: Complete Investigation

```bash
# 1. Create a case directory
CASE_ID="CASE-$(date +%Y%m%d-%H%M%S)"

# 2. Run full collection
sudo vivisect collect $CASE_ID

# 3. Create memory dump
sudo vivisect memory dump --output ${CASE_ID}_memory.raw

# 4. Capture network traffic (background)
sudo vivisect network capture eth0 ${CASE_ID}_network.pcap --duration 600 &

# 5. Image a suspicious drive
sudo vivisect disk image /dev/sdc ${CASE_ID}_disk.img --method dcfldd

# 6. Generate final reports
sudo vivisect report $CASE_ID --format html
sudo vivisect report $CASE_ID --format json

# 7. View results
ls -lh /var/lib/vivisect/output/${CASE_ID}*
```

## Need Help?

- Full documentation: `README.md`
- Command help: `vivisect <command> --help`
- View logs: `sudo tail -f /var/log/vivisect/main.log`

Happy forensicating!
