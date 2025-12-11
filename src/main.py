#!/usr/bin/env python3
"""
Vivisect - Digital Forensics Suite
Main entry point for the application
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cli import main

if __name__ == '__main__':
    sys.exit(main())
