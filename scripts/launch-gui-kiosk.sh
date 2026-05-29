#!/bin/bash
# Vivisect GUI Kiosk Mode Launcher
# Launches the NATIVE Kivy GUI full-screen on the onboard display.
#
# Unlike the legacy web kiosk, this opens NO network listener and runs NO
# browser — the GUI talks to the forensics engine directly, in-process.
# (The web GUI under src/web still exists but is not started here.)

set -e

echo "Starting Vivisect native GUI in kiosk mode..."

DISPLAY_NUM="${DISPLAY:-:0}"

# Wait for display server
echo "Waiting for display server..."
timeout=30
while [ $timeout -gt 0 ]; do
    if xdpyinfo -display $DISPLAY_NUM >/dev/null 2>&1; then
        echo "Display server is ready"
        break
    fi
    sleep 1
    timeout=$((timeout - 1))
done

if [ $timeout -eq 0 ]; then
    echo "Error: Display server did not start"
    exit 1
fi

# Disable screen blanking and power management
xset -display $DISPLAY_NUM s off
xset -display $DISPLAY_NUM -dpms
xset -display $DISPLAY_NUM s noblank

# Hide mouse cursor after 3 seconds of inactivity (optional)
unclutter -display $DISPLAY_NUM -idle 3 -root &

# Launch the native GUI full-screen. Kivy manages its own window; no browser.
cd /opt/vivisect/src
export VIVISECT_GUI_FULLSCREEN=1
exec python3 -m gui
