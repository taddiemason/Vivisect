#!/bin/bash
# USB Gadget Monitor Service
# Monitors USB connection and triggers actions

LOGFILE="/var/log/vivisect/usb-monitor.log"
PIDFILE="/var/run/usb-gadget-monitor.pid"

# Write PID
echo $$ > "$PIDFILE"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOGFILE"
}

log "USB Gadget Monitor started"

# Monitor usb0 interface state
while true; do
    # Check if usb0 exists and is up
    if ip link show usb0 2>/dev/null | grep -q "state UP"; then
        # Check if we've already started capture
        if [ ! -f /var/run/usb-capture.pid ]; then
            log "USB connection detected - starting forensics collection"

            # Create case ID
            CASE_ID="USB_$(date +%Y%m%d_%H%M%S)"

            # Start packet capture
            CAPTURE_FILE="/var/lib/vivisect/output/${CASE_ID}_capture.pcap"
            tcpdump -i usb0 -w "$CAPTURE_FILE" -n 2>/dev/null &
            CAPTURE_PID=$!
            echo $CAPTURE_PID > /var/run/usb-capture.pid

            log "Packet capture started (PID: $CAPTURE_PID, File: $CAPTURE_FILE)"

            # Get host MAC address
            sleep 2
            HOST_MAC=$(ip neigh show dev usb0 | awk '{print $5}' | head -1)
            if [ -n "$HOST_MAC" ]; then
                log "Host MAC address: $HOST_MAC"
            fi

            # Notify GUI
            if pgrep -f "python.*web.app" > /dev/null; then
                echo "connected" > /tmp/usb-status
                log "Notified GUI of USB connection"
            fi

            # Run auto-collection if enabled
            if [ -f /etc/vivisect/vivisect.conf ]; then
                if grep -q '"usb_auto_collect".*true' /etc/vivisect/vivisect.conf; then
                    log "Running automatic collection..."
                    /usr/local/bin/vivisect collect "$CASE_ID" >> "$LOGFILE" 2>&1 &
                fi
            fi
        fi
    else
        # USB disconnected
        if [ -f /var/run/usb-capture.pid ]; then
            CAPTURE_PID=$(cat /var/run/usb-capture.pid)
            if kill -0 $CAPTURE_PID 2>/dev/null; then
                log "USB disconnected - stopping packet capture (PID: $CAPTURE_PID)"
                kill $CAPTURE_PID 2>/dev/null
            fi
            rm -f /var/run/usb-capture.pid

            # Notify GUI
            echo "disconnected" > /tmp/usb-status
        fi
    fi

    # Check every 2 seconds
    sleep 2
done
