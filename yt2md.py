#!/usr/bin/env python3
"""
youtube-to-markdown: Direct executable entrypoint.
Usage:
    python yt2md.py <URL> [options]
"""

import sys
import os

# Ensure package is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from yt2md.cli import main

if __name__ == "__main__":
    main()
