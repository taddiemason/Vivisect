# Vivisect Native GUI (no browser, no network listener)

The native GUI is a [Kivy](https://kivy.org) desktop/touch application that talks
directly to the Vivisect engine **in-process**. It is the default interface for
onboard displays and kiosk mode.

## Why native (security)

For a forensics device that gets plugged into hostile or evidence networks, the
biggest attack surface is an always-on web server plus a browser engine. The
native GUI removes all of it:

| | Web GUI (`src/web`) | Native GUI (`src/gui`) |
|---|---|---|
| Listening TCP port | Yes (`0.0.0.0:5000`) | **None** |
| Browser / webview engine | Yes | **None** |
| JavaScript runtime | Yes | **None** |
| Auth token / CORS | Required | **Not applicable** |
| Talks to engine | Over HTTP/WebSocket | **Direct Python calls** |

Nothing in `src/web` was removed — it simply isn't started. To run the legacy web
GUI you must launch it explicitly (`python3 -m web.app`).

## Install

```bash
# Base forensics tool
pip install -r requirements.txt        # (web stack — optional for native)
# Native GUI dependency
pip install -r requirements-gui.txt     # kivy>=2.3.0
# …or, via setup.py extras:
pip install -e .[gui]
```

## Run

```bash
# From the src/ directory:
python3 -m gui

# Installed console entry point:
vivisect-gui-native

# Full-screen kiosk on an onboard display:
VIVISECT_GUI_FULLSCREEN=1 python3 -m gui
#   …or just run the kiosk launcher / enable the systemd service:
sudo ./scripts/launch-gui-kiosk.sh
```

Set `VIVISECT_GUI_FULLSCREEN=1` for kiosk/onboard displays; unset (default) opens a
1024×640 window for desktop use.

## Tabs

Full parity with the web GUI: **Dashboard** (quick collection, system status, quick
actions, USB mode switching, activity log), **Disk** (list devices, create dd/dcfldd
image), **Network** (list interfaces, capture), **Memory** (analyze live system,
create dump), **Artifacts** (browser/logs/persistence), **HID** (status, mode switch,
send string, execute payload — authorized use only), and **Reports** (list and open).

## Architecture notes

- All backend calls run on the engine's existing thread pool
  (`engine.tasks.submit`); results are marshalled back to the Kivy main thread via
  `Clock.schedule_once`. The UI never blocks.
- Reports are HTML (Chart.js) and are opened with the OS default handler rather than
  an embedded webview, so the GUI itself stays web-engine-free.
- The forensic modules shell out to Linux tools (`dd`, `tcpdump`, `/var/log`, etc.),
  so full functionality is on the Debian/Raspberry Pi target. On a Windows/macOS dev
  box the UI runs and renders, but Linux-only operations return a clean error in the
  activity log rather than crashing.
