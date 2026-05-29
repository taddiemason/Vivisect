#!/usr/bin/env python3
"""Standalone web server launcher for Vivisect GUI"""

import sys
import os

# Add parent directory to path (resolve symlinks for proper imports)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from web.app import create_app

if __name__ == '__main__':
    app, socketio = create_app()

    host = os.environ.get('VIVISECT_WEB_HOST') or app.config['VIVISECT_HOST']
    port = int(os.environ.get('VIVISECT_WEB_PORT') or app.config['VIVISECT_PORT'])
    token = app.config['VIVISECT_TOKEN']
    is_loopback_bind = host in ('127.0.0.1', 'localhost', '::1')

    print("="*60)
    print("Vivisect Web GUI Server")
    print("="*60)
    print(f"Server running on: http://{host}:{port}")
    print(f"Access from browser: http://localhost:{port}")
    if not is_loopback_bind:
        print("")
        print("  ⚠  WARNING: bound to a non-loopback address — the GUI is")
        print("     reachable over the network. The API token below is")
        print("     required for all remote requests.")
    if app.config['VIVISECT_TOKEN_GENERATED']:
        print("")
        print(f"  API token (generated): {token}")
        print(f"  Remote access: http://{host}:{port}/?token={token}")
        print("  Set web.auth_token (or VIVISECT_AUTH_TOKEN) for a stable token.")
    print("Press Ctrl+C to stop")
    print("="*60)

    socketio.run(app, host=host, port=port, debug=False, allow_unsafe_werkzeug=True)
