"""
yt2md.subtitles - Zero-cost, sub-second native caption (CC) extraction.
Fetches manual or auto-generated subtitles directly via yt-dlp metadata without audio download.
"""

import json
import os
import re
import urllib.request
from typing import Dict, List, Optional, Tuple


def _time_to_seconds(time_str: str) -> float:
    """Convert timestamp string (HH:MM:SS.mmm or MM:SS.mmm) to seconds."""
    parts = time_str.strip().split(":")
    if len(parts) == 3:
        h, m, s = parts
        return float(h) * 3600 + float(m) * 60 + float(s)
    elif len(parts) == 2:
        m, s = parts
        return float(m) * 60 + float(s)
    return float(parts[0])


def parse_vtt(vtt_content: str) -> List[Dict]:
    """
    Parses WebVTT content into structured segments:
    [{ 'start': float, 'end': float, 'text': str }]
    Cleans up duplicate words, rolling caption artifacts, and formatting tags.
    """
    lines = vtt_content.splitlines()
    segments = []
    
    # Regex for timestamp line: 00:00:01.000 --> 00:00:04.500
    ts_pattern = re.compile(
        r"(\d{1,2}:)?\d{2}:\d{2}\.\d{3}\s+-->\s+(\d{1,2}:)?\d{2}:\d{2}\.\d{3}"
    )

    current_start = None
    current_end = None
    current_text_lines = []

    for line in lines:
        line_strip = line.strip()
        if not line_strip or line_strip.startswith("WEBVTT") or line_strip.startswith("NOTE"):
            continue

        match = ts_pattern.search(line_strip)
        if match:
            # Flush previous segment if valid
            if current_start is not None and current_text_lines:
                clean_text = " ".join(current_text_lines).strip()
                # Clean up html tags like <c> or </c> or <00:00:00.000>
                clean_text = re.sub(r"<[^>]+>", "", clean_text).strip()
                if clean_text and (not segments or segments[-1]["text"] != clean_text):
                    segments.append({
                        "start": current_start,
                        "end": current_end,
                        "text": clean_text
                    })
                current_text_lines = []

            # Parse start and end times
            times = re.findall(r"(\d{1,2}:)?\d{2}:\d{2}\.\d{3}", match.group(0))
            if len(times) >= 2:
                # Re-extract raw strings matching the split
                raw_times = line_strip.split("-->")
                current_start = _time_to_seconds(raw_times[0].split()[0])
                current_end = _time_to_seconds(raw_times[1].split()[0])
        else:
            # Subtitle text line
            if current_start is not None:
                # Remove inline tags
                clean_line = re.sub(r"<[^>]+>", "", line_strip).strip()
                if clean_line and clean_line not in current_text_lines:
                    current_text_lines.append(clean_line)

    # Flush final segment
    if current_start is not None and current_text_lines:
        clean_text = " ".join(current_text_lines).strip()
        clean_text = re.sub(r"<[^>]+>", "", clean_text).strip()
        if clean_text and (not segments or segments[-1]["text"] != clean_text):
            segments.append({
                "start": current_start,
                "end": current_end,
                "text": clean_text
            })

    return segments


def extract_native_subtitles(
    info_dict: dict,
    preferred_langs: Tuple[str, ...] = ("pt", "pt-BR", "en", "es"),
    output_dir: Optional[str] = None
) -> Optional[Dict]:
    """
    Attempts to download and parse native human subtitles or auto-captions (CC).
    Returns None if no captions are present.
    """
    subtitles = info_dict.get("subtitles") or {}
    auto_captions = info_dict.get("automatic_captions") or {}

    if not subtitles and not auto_captions:
        return None

    selected_lang = None
    selected_track = None
    is_auto = False

    # 1. Try human subtitles in preferred languages
    for lang in preferred_langs:
        for available_lang in subtitles:
            if available_lang.lower().startswith(lang.lower()):
                selected_lang = available_lang
                selected_track = subtitles[available_lang]
                is_auto = False
                break
        if selected_track:
            break

    # 2. If no human subtitles, try auto captions in preferred languages
    if not selected_track:
        for lang in preferred_langs:
            for available_lang in auto_captions:
                if available_lang.lower().startswith(lang.lower()):
                    selected_lang = available_lang
                    selected_track = auto_captions[available_lang]
                    is_auto = True
                    break
            if selected_track:
                break

    # 3. Fallback to any available language
    if not selected_track:
        if subtitles:
            selected_lang = list(subtitles.keys())[0]
            selected_track = subtitles[selected_lang]
            is_auto = False
        elif auto_captions:
            selected_lang = list(auto_captions.keys())[0]
            selected_track = auto_captions[selected_lang]
            is_auto = True

    if not selected_track:
        return None

    # Find VTT format track URL
    vtt_url = None
    for entry in selected_track:
        ext = entry.get("ext")
        if ext == "vtt":
            vtt_url = entry.get("url")
            break
    if not vtt_url and selected_track:
        vtt_url = selected_track[0].get("url")

    if not vtt_url:
        return None

    try:
        req = urllib.request.Request(
            vtt_url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            vtt_raw = response.read().decode("utf-8", errors="replace")

        segments = parse_vtt(vtt_raw)
        if not segments:
            return None

        # Build full text
        full_text = " ".join(seg["text"] for seg in segments)

        result = {
            "source": "native_cc",
            "is_auto": is_auto,
            "language": selected_lang,
            "segments": segments,
            "full_text": full_text
        }

        # Optionally save raw files
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            vtt_path = os.path.join(output_dir, "subtitles.vtt")
            with open(vtt_path, "w", encoding="utf-8") as f:
                f.write(vtt_raw)

            json_path = os.path.join(output_dir, "subtitles.json")
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

        return result

    except Exception:
        return None
