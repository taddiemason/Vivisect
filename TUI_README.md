# Vivisect Terminal UI

A browser-free front end for Vivisect built with [Textual](https://textual.textualize.io/).
It runs in any terminal — the on-device console, an SSH session, or the USB
serial console the device already exposes — and talks **directly** to
`VivisectEngine`, so there is no network service to secure and a much smaller
attack surface than the web GUI.

## Why a TUI

- **Works everywhere a terminal does:** device screen, SSH, or `screen /dev/ttyACM0`
  over the USB serial gadget.
- **Lightweight:** no Chromium/X kiosk — suitable for a Pi-class device.
- **Same engine:** shares config, logging, the module set, and the unified
  `collect` workflow with the CLI and web GUI.

## Install

```bash
pip install -e .[tui]      # or: pip install textual>=0.50.0
```

## Run

```bash
# Directly
python src/tui/app.py

# Or via the installed entry point
vivisect-tui
```

Most operations need root (block-device and memory access), the same as the CLI
and web GUI.

### Access methods

| Method | How |
|--------|-----|
| On-device screen | `systemctl enable --now vivisect-tui` (runs on tty1, see `systemd/vivisect-tui.service`) |
| SSH | `ssh root@device` then `vivisect-tui` |
| USB serial gadget | From the host: `screen /dev/ttyACM0 115200` (or `minicom`), log in, run `vivisect-tui` |

## Features (prototype)

- **Dashboard** — module enabled-state, output/log directories, worker count.
- **Devices** — block devices (`lsblk`) and network interfaces (`ip`), loaded on
  a worker thread so the UI never blocks.
- **Collect** — run a full forensic collection with live per-step progress and
  the resulting report paths.
- **Tasks** — recent background tasks and their state.
- **Activity log** — timestamped log panel.

Key bindings: `r` refresh · `c` jump to Collect · `q` quit.

## Status

This is a proof-of-concept front end demonstrating that the engine refactor lets
any interface drive Vivisect. It does not yet cover every operation the web GUI
exposes (e.g. disk imaging parameters, packet capture, USB HID). Those map
cleanly onto the same `engine` calls and can be added incrementally.
