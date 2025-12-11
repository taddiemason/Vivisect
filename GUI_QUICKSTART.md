# Vivisect GUI - Quick Start for Onboard Display

## 🖥️ What You Get

A **full-screen forensics interface** that launches automatically on your device's onboard screen.

## ⚡ Quick Setup (2 Commands)

```bash
# 1. Install Vivisect with GUI
sudo ./scripts/install.sh
# When asked: "Enable GUI kiosk mode on boot?" → Press 'y'

# 2. Reboot device
sudo reboot
```

**That's it!** The GUI will launch automatically in full-screen kiosk mode.

## 🎯 What You See on the Screen

### Main Dashboard
```
┌─────────────────────────────────────────────────────┐
│  🔍 Vivisect Forensics          ● Connected  12:34  │
├─────────────────────────────────────────────────────┤
│  [Dashboard] [Disk] [Network] [Memory] [Artifacts]  │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────────────┐  ┌──────────────────┐        │
│  │ Quick Collection │  │  System Status    │        │
│  │                  │  │  Active: 0        │        │
│  │  [Case ID]       │  │  Output: /var/... │        │
│  │                  │  │                   │        │
│  │ [Start          │  └──────────────────┘        │
│  │  Collection]    │                                │
│  └──────────────────┘  ┌──────────────────┐        │
│                        │  Quick Actions    │        │
│  ┌──────────────────┐  │                   │        │
│  │  Activity Log    │  │  [Analyze Memory] │        │
│  │  Connected...    │  │  [Extract Browser]│        │
│  │  System ready    │  │  [System Logs]    │        │
│  └──────────────────┘  └──────────────────┘        │
│                                                      │
└─────────────────────────────────────────────────────┘
```

### Touch-Friendly Interface
- **Large Buttons**: Easy to tap (50px+ height)
- **Clear Icons**: Visual indicators for all functions
- **Real-Time Updates**: Live progress bars
- **Tab Navigation**: Switch between modules
- **Dark Theme**: Reduces eye strain

## 📱 Using the Touch Screen

### Run Forensics Collection
1. **Tap** "Dashboard" tab
2. **Tap** in "Case ID" field (optional - auto-generates if empty)
3. **Tap** "Start Collection" button
4. Watch progress in real-time
5. Reports saved to `/var/lib/vivisect/output/`

### Create Disk Image
1. **Tap** "Disk" tab
2. **Tap** "Refresh Devices"
3. **Tap** a device from the list
4. Enter output filename
5. **Tap** "Create Disk Image"

### Capture Network Traffic
1. **Tap** "Network" tab
2. **Tap** interface to select
3. Set duration
4. **Tap** "Start Capture"

### Analyze Memory
1. **Tap** "Memory" tab
2. **Tap** "Analyze Running System"
3. View results instantly

### Extract Artifacts
1. **Tap** "Artifacts" tab
2. **Tap** any extraction button:
   - Browser History
   - System Logs
   - Persistence Mechanisms
3. View results on screen

## 🔌 Physical Setup

### For Portable Forensics Device

```
┌─────────────────────────────────────┐
│  Forensics Device (Debian/Kali)    │
│  ┌──────────────────────────────┐  │
│  │  7"+ Touchscreen Display     │  │  ← GUI shows here
│  │  1920x1080 recommended       │  │
│  └──────────────────────────────┘  │
│                                     │
│  ● Power Button                     │
│  ● USB Ports (for evidence drives)  │
│  ● Network Port                     │
└─────────────────────────────────────┘
```

### On Boot:
1. Device powers on
2. X server starts
3. Vivisect GUI launches in full-screen
4. Touchscreen ready for forensics work

## 🌐 Access from Other Computers

The GUI is also accessible from browsers on your network:

```bash
# Find device IP
ip addr show

# Access from any computer's browser
http://[device-ip]:5000
```

Example: `http://192.168.1.100:5000`

## 🎛️ Manual Control

### Start GUI Manually
```bash
# Start web server only (access via browser)
sudo vivisect-gui

# Start in kiosk mode (full-screen)
sudo launch-gui-kiosk
```

### Service Control
```bash
# Start GUI service
sudo systemctl start vivisect-gui

# Stop GUI service
sudo systemctl stop vivisect-gui

# Check status
sudo systemctl status vivisect-gui

# Enable on boot
sudo systemctl enable vivisect-gui

# Disable on boot
sudo systemctl disable vivisect-gui
```

## 📊 Typical Workflow

### Field Forensics Collection

```
1. Power on device
   ↓
2. GUI auto-launches on screen
   ↓
3. Tap "Start Collection"
   ↓
4. Watch real-time progress:
   - Analyzing memory ✓
   - Extracting browser history ✓
   - Collecting logs ✓
   - Finding persistence ✓
   ↓
5. Reports generated automatically
   ↓
6. Tap "Reports" tab to view/download
```

### Live System Analysis

```
1. Connect to suspect device network
   ↓
2. Tap "Network" → "Refresh Interfaces"
   ↓
3. Select interface
   ↓
4. Start packet capture (60s)
   ↓
5. While capturing:
   - Tap "Memory" tab
   - Tap "Analyze Running System"
   ↓
6. View all results on dashboard
```

## 🔧 Customization

### Change Display Resolution

Edit `/usr/local/bin/launch-gui-kiosk`:
```bash
# Add before browser launch:
xrandr --output HDMI-1 --mode 1920x1080
```

### Auto-Launch Specific Tab

Edit `src/web/templates/index.html`:
```javascript
// In DOMContentLoaded, add:
showTab('dashboard');  // Change to: 'disk', 'network', etc.
```

### Hide Mouse Cursor Immediately

Edit `/usr/local/bin/launch-gui-kiosk`:
```bash
# Change:
unclutter -display $DISPLAY_NUM -idle 3 -root &
# To:
unclutter -display $DISPLAY_NUM -idle 0 -root &
```

## 💡 Pro Tips

1. **Quick Reboot**: If GUI freezes, SSH in and:
   ```bash
   sudo systemctl restart vivisect-gui
   ```

2. **Remote Debugging**: Access from laptop to test before field deployment

3. **Save Templates**: Create case ID templates for common scenarios

4. **Evidence Backup**: Mount USB drive and reports auto-save to `/var/lib/vivisect/output/`

5. **Screen Brightness**: Adjust for field use:
   ```bash
   echo 50 > /sys/class/backlight/*/brightness  # 0-100
   ```

## ⚠️ Important Notes

- **Root Required**: GUI runs as root for forensics access
- **Firewall**: Port 5000 is open on all interfaces
- **No Auth Yet**: No password protection (physical security important!)
- **Single User**: One operator at a time

## 🆘 Troubleshooting

### Black Screen on Boot
```bash
# SSH into device
sudo systemctl status vivisect-gui
sudo journalctl -u vivisect-gui -n 50

# Restart
sudo systemctl restart vivisect-gui
```

### Touchscreen Not Responding
```bash
# Check X server
echo $DISPLAY

# Restart X and GUI
sudo systemctl restart lightdm  # or gdm3/sddm
sudo systemctl restart vivisect-gui
```

### Can't Access Remotely
```bash
# Allow through firewall
sudo ufw allow 5000

# Check if server is running
sudo netstat -tulpn | grep 5000
```

## 📦 Hardware Recommendations

### Budget Build (~$200)
- Raspberry Pi 4 (4GB RAM)
- 7" Official Touch Display
- 64GB SD Card
- Case with display mount

### Professional Build (~$800)
- Intel NUC or similar
- 15" Capacitive Touch Monitor
- 256GB+ NVMe SSD
- Ruggedized case

### Enterprise Build (~$2000+)
- Panasonic Toughbook with touch
- Pre-installed and hardened
- Field-ready

## 🚀 Next Steps

1. ✅ Install Vivisect with GUI
2. ✅ Enable kiosk mode
3. ✅ Reboot and test
4. 📖 Read [GUI_README.md](GUI_README.md) for advanced features
5. 🔒 Configure firewall for your network
6. 📝 Create case templates
7. 🎯 Deploy in field!

---

**The GUI makes Vivisect forensics accessible with just a tap!** 🎯
