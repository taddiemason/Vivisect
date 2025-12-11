# Vivisect Web GUI - Onboard Display Mode

This guide explains how to use the Vivisect Web GUI, especially for devices with onboard displays.

## Features

The Vivisect Web GUI provides:

✅ **Touch-Friendly Interface** - Optimized for touchscreen displays
✅ **Kiosk Mode** - Full-screen forensics interface on device boot
✅ **Real-Time Updates** - Live progress tracking via WebSockets
✅ **Dashboard** - Quick access to all forensics modules
✅ **Remote Access** - Access from any browser on the network

## Installation

The GUI is automatically installed with Vivisect. During installation, you'll be asked:

```
Do you want to enable GUI kiosk mode on boot? (y/n)
```

- **Yes (y)**: GUI will launch automatically on boot in full-screen kiosk mode
- **No (n)**: GUI can be started manually when needed

## Starting the GUI

### Option 1: Auto-Start on Boot (Kiosk Mode)

If you enabled kiosk mode during installation:

1. Power on the device
2. GUI automatically launches in full-screen mode
3. Access forensics tools via touchscreen

To enable/disable kiosk mode:

```bash
# Enable
sudo systemctl enable vivisect-gui.service

# Disable
sudo systemctl disable vivisect-gui.service

# Start now
sudo systemctl start vivisect-gui.service

# Stop
sudo systemctl stop vivisect-gui.service
```

### Option 2: Manual Start (Server Mode)

Start the web server manually:

```bash
# Start web GUI server
sudo vivisect-gui
```

Then access from browser:
- **Local**: http://localhost:5000
- **Network**: http://[device-ip]:5000

### Option 3: Launch Kiosk Mode Manually

```bash
# Launch in kiosk mode
sudo launch-gui-kiosk
```

## Using the GUI

### Dashboard

The main dashboard provides:

- **Quick Collection**: Run full forensics collection with one click
- **System Status**: View active tasks and system info
- **Quick Actions**: Direct access to common operations
- **Activity Log**: Real-time log of all operations

### Tabs

**Disk Imaging**
- List available devices
- Create forensic disk images
- View device information

**Network**
- List network interfaces
- Capture traffic to PCAP
- Monitor network activity

**Memory**
- Analyze running system
- Create memory dumps
- View process information

**Artifacts**
- Extract browser history
- Collect system logs
- Find persistence mechanisms

**Reports**
- View generated reports
- Download forensics data
- Access case files

### Touch Gestures

The interface is optimized for touch:

- **Tap** - Select items and buttons
- **Scroll** - Navigate lists and logs
- **Long Press** - (Future: Context menus)

All buttons and inputs have large touch targets (minimum 50px height).

## Configuration

### Display Settings

For optimal display on your onboard screen, edit `/usr/local/bin/launch-gui-kiosk`:

```bash
# Set your display resolution
DISPLAY_NUM=":0"  # Change if using different display

# Screen blanking (default: off)
xset -display $DISPLAY_NUM s off
xset -display $DISPLAY_NUM -dpms
```

### Browser Selection

The kiosk launcher tries browsers in this order:
1. Chromium (recommended for kiosk mode)
2. Chrome
3. Firefox

To force a specific browser, edit the launch script.

### Server Port

Change the web server port in `/opt/vivisect/src/web/run_server.py`:

```python
socketio.run(app, host='0.0.0.0', port=5000)  # Change 5000 to your port
```

### Network Access

By default, the GUI is accessible on all network interfaces (`0.0.0.0:5000`).

To restrict to localhost only:
```python
socketio.run(app, host='127.0.0.1', port=5000)
```

## Hardware Recommendations

### Onboard Display

**Minimum:**
- Resolution: 800x600
- Touchscreen: Optional but recommended

**Recommended:**
- Resolution: 1920x1080 or higher
- Touchscreen: Capacitive multi-touch
- Size: 7" or larger for better usability

### Device Specifications

**Minimum:**
- CPU: Dual-core 1.5GHz
- RAM: 4GB
- Storage: 32GB
- Display: Any with X11 support

**Recommended:**
- CPU: Quad-core 2.0GHz+
- RAM: 8GB+
- Storage: 256GB+ SSD
- Display: Multi-touch LCD

## Troubleshooting

### GUI Won't Start

```bash
# Check service status
sudo systemctl status vivisect-gui.service

# View logs
sudo journalctl -u vivisect-gui -n 50

# Test manually
sudo vivisect-gui
```

### Display Issues

```bash
# Check X server
echo $DISPLAY

# List displays
xrandr

# Reset X authority
sudo rm ~/.Xauthority
sudo systemctl restart vivisect-gui
```

### Browser Won't Launch

```bash
# Install chromium
sudo apt-get install chromium-browser

# Test browser
chromium-browser --version

# Check kiosk script permissions
ls -l /usr/local/bin/launch-gui-kiosk
```

### Can't Access from Network

```bash
# Check firewall
sudo ufw status
sudo ufw allow 5000

# Check port binding
sudo netstat -tulpn | grep 5000

# Test connection
curl http://localhost:5000
```

### Touchscreen Not Working

```bash
# Install touchscreen support
sudo apt-get install xinput

# List input devices
xinput list

# Calibrate (if needed)
sudo apt-get install xinput-calibrator
xinput_calibrator
```

## Security Considerations

⚠️ **Important**: The web GUI runs with root privileges to access forensics data.

**Security Best Practices:**

1. **Firewall**: Restrict port 5000 to trusted networks
   ```bash
   sudo ufw deny 5000
   sudo ufw allow from 192.168.1.0/24 to any port 5000
   ```

2. **VPN**: Access remotely only through VPN

3. **Authentication**: Currently no authentication (planned for future)

4. **HTTPS**: Consider setting up reverse proxy with SSL

5. **Physical Security**: Secure device physically if used in field

## Remote Access

Access the GUI from another computer on the same network:

1. Find device IP:
   ```bash
   ip addr show
   ```

2. Access from browser:
   ```
   http://[device-ip]:5000
   ```

3. For permanent access, set static IP

## Customization

### Change Theme Colors

Edit `/opt/vivisect/src/web/static/css/style.css`:

```css
:root {
    --primary: #2563eb;      /* Change primary color */
    --dark: #0f172a;         /* Change background */
    --text: #f1f5f9;         /* Change text color */
}
```

### Add Custom Buttons

Edit `/opt/vivisect/src/web/templates/index.html` to add custom quick actions.

### Modify Dashboard

The dashboard is modular - add/remove cards in the HTML template.

## Advanced: Raspberry Pi Setup

Perfect for portable forensics devices:

```bash
# 1. Flash Raspberry Pi OS
# 2. Enable SSH
# 3. Install Vivisect
git clone https://github.com/taddiemason/Vivisect.git
cd Vivisect
sudo ./scripts/install.sh

# 4. Enable kiosk mode
sudo systemctl enable vivisect-gui.service

# 5. Configure auto-login (optional)
sudo raspi-config
# Navigate to: System Options → Boot / Auto Login → Desktop Autologin
```

## Known Limitations

- No authentication system (yet)
- Single user at a time
- No concurrent operations UI
- Limited mobile browser support (use kiosk mode)

## Future Enhancements

Planned features:
- [ ] User authentication
- [ ] Multi-user support
- [ ] Enhanced data visualization
- [ ] Drag-and-drop file analysis
- [ ] Mobile-optimized responsive layout
- [ ] Dark/light theme toggle
- [ ] Customizable dashboard widgets

## Support

For GUI-specific issues:

1. Check logs: `/var/log/vivisect/`
2. Browser console: Press F12 in browser
3. Service status: `sudo systemctl status vivisect-gui`
4. Test manually: `sudo vivisect-gui`

## Examples

### Complete Kiosk Setup

```bash
# 1. Install
sudo ./scripts/install.sh
# Select 'y' for kiosk mode

# 2. Reboot
sudo reboot

# 3. GUI automatically launches

# 4. Run forensics collection
# Tap "Start Collection" on dashboard
```

### Remote Forensics Workstation

```bash
# On forensics device:
sudo vivisect-gui

# On analyst workstation:
# Open browser to http://[device-ip]:5000
# Perform analysis remotely
```

### Automated Evidence Collection

```bash
# Set up unattended kiosk that auto-collects on boot
# Edit /etc/rc.local or create systemd service:

[Unit]
Description=Auto Forensics Collection
After=vivisect-gui.service

[Service]
Type=oneshot
ExecStart=/usr/bin/curl -X POST http://localhost:5000/api/collect \
    -H "Content-Type: application/json" \
    -d '{"case_id":"AUTO-'$(date +%Y%m%d-%H%M%S)'"}'

[Install]
WantedBy=multi-user.target
```

---

**Ready to use Vivisect GUI on your forensics device!**

For general Vivisect documentation, see [README.md](README.md)
