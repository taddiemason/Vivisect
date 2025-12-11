#!/bin/bash
# Vivisect GUI Kiosk Mode Launcher
# Launches the web GUI in full-screen kiosk mode on the onboard display

set -e

echo "Starting Vivisect GUI in Kiosk Mode..."

# Configuration
VIVISECT_PORT=5000
VIVISECT_URL="http://localhost:${VIVISECT_PORT}"
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

# Start Vivisect web server in background
echo "Starting Vivisect web server..."
cd /opt/vivisect/src
python3 -m web.app &
WEB_PID=$!

# Wait for web server to be ready
echo "Waiting for web server..."
timeout=60
while [ $timeout -gt 0 ]; do
    if curl -s $VIVISECT_URL >/dev/null 2>&1; then
        echo "Web server is ready"
        break
    fi
    sleep 1
    timeout=$((timeout - 1))
done

if [ $timeout -eq 0 ]; then
    echo "Error: Web server did not start"
    kill $WEB_PID 2>/dev/null || true
    exit 1
fi

# Disable screen blanking and power management
xset -display $DISPLAY_NUM s off
xset -display $DISPLAY_NUM -dpms
xset -display $DISPLAY_NUM s noblank

# Hide mouse cursor after 3 seconds of inactivity (optional)
unclutter -display $DISPLAY_NUM -idle 3 -root &

# Launch browser in kiosk mode
# Try different browsers in order of preference
if command -v chromium-browser >/dev/null 2>&1; then
    echo "Launching with Chromium..."
    chromium-browser \
        --kiosk \
        --noerrdialogs \
        --disable-infobars \
        --no-first-run \
        --disable-session-crashed-bubble \
        --disable-translate \
        --disable-features=TranslateUI \
        --touch-events=enabled \
        --display=$DISPLAY_NUM \
        $VIVISECT_URL

elif command -v google-chrome >/dev/null 2>&1; then
    echo "Launching with Chrome..."
    google-chrome \
        --kiosk \
        --noerrdialogs \
        --disable-infobars \
        --no-first-run \
        --touch-events=enabled \
        --display=$DISPLAY_NUM \
        $VIVISECT_URL

elif command -v firefox >/dev/null 2>&1; then
    echo "Launching with Firefox..."
    firefox \
        --kiosk \
        --display=$DISPLAY_NUM \
        $VIVISECT_URL

else
    echo "Error: No suitable browser found"
    echo "Please install chromium-browser, google-chrome, or firefox"
    kill $WEB_PID 2>/dev/null || true
    exit 1
fi

# If browser exits, stop web server
echo "Browser closed, stopping web server..."
kill $WEB_PID 2>/dev/null || true
