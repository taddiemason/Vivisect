#!/usr/bin/env python3
"""Standalone web server launcher for Vivisect GUI"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

if __name__ == '__main__':
    app, socketio = create_app()
    print("="*60)
    print("Vivisect Web GUI Server")
    print("="*60)
    print(f"Server running on: http://0.0.0.0:5000")
    print(f"Access from browser: http://localhost:5000")
    print("Press Ctrl+C to stop")
    print("="*60)

    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
