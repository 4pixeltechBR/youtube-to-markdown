"""
yt2md.utils - System helpers, path sanitizers, and binary locators.
"""

import os
import re
import sys
import shutil
import warnings
from pathlib import Path
from typing import Optional

# Suppress benign third-party library warnings to keep CLI/JSON streams clean
warnings.filterwarnings("ignore", category=UserWarning)
try:
    from requests.exceptions import RequestsDependencyWarning
    warnings.filterwarnings("ignore", category=RequestsDependencyWarning)
except ImportError:
    pass


def ensure_utf8_io():
    """Ensure standard input and output use UTF-8 encoding across Windows/Linux/macOS."""
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    if sys.stderr and hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass


def sanitize_filename(name: str, max_length: int = 100) -> str:
    """
    Sanitize string to be safe for directory and file names across Windows, Linux, and macOS.
    Removes reserved characters and trims length.
    """
    if not name:
        return "untitled"

    # Replace forbidden Windows characters: <>:"/\|?*
    clean = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", name)
    # Replace multiple whitespace/tabs with single space
    clean = re.sub(r"\s+", " ", clean).strip()

    # Reserved Windows names
    reserved = {
        "CON", "PRN", "AUX", "NUL",
        "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
        "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
    }
    if clean.upper() in reserved:
        clean = f"_{clean}"

    if len(clean) > max_length:
        clean = clean[:max_length].rstrip(" .")

    return clean or "untitled"


def format_timestamp(seconds: float) -> str:
    """Format seconds into HH:MM:SS or MM:SS format."""
    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def get_ffmpeg_binary() -> Optional[str]:
    """
    Locates FFmpeg executable in the system PATH.
    Falls back automatically to imageio-ffmpeg embedded binary if available.
    """
    # 1. System PATH
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        return ffmpeg_path

    # 2. Check imageio_ffmpeg
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        pass

    return None


def to_file_uri(path: str | Path) -> str:
    """Convert a local path to a clickable file:/// URI for markdown preview."""
    abs_path = os.path.abspath(path).replace("\\", "/")
    if not abs_path.startswith("/"):
        abs_path = f"/{abs_path}"
    return f"file://{abs_path}"
