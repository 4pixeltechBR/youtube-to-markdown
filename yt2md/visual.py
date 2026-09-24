"""
yt2md.visual - 16-frame visual timeline extractor.
Downloads optimized video and extracts 16 equidistant frames using FFmpeg.
"""

import os
import subprocess
from typing import Dict, List, Optional

from .utils import format_timestamp, get_ffmpeg_binary


def extract_visual_timeline(
    video_path: str,
    duration: float,
    output_dir: str,
    num_frames: int = 16,
    transcript_segments: Optional[List[Dict]] = None
) -> List[Dict]:
    """
    Extracts equidistant visual frames across the media duration using FFmpeg.
    Associates each frame with spoken dialogue occurring at that timestamp.
    """
    ffmpeg_bin = get_ffmpeg_binary()
    if not ffmpeg_bin:
        raise RuntimeError("FFmpeg executable not found. Cannot extract visual frames.")

    frames_dir = os.path.join(output_dir, "frames")
    os.makedirs(frames_dir, exist_ok=True)

    if duration <= 0:
        duration = 60.0  # Safe default if duration couldn't be parsed

    step = duration / (num_frames + 1)
    frames_info = []

    for i in range(1, num_frames + 1):
        ts = round(i * step, 2)
        sec_int = int(ts)
        time_str = format_timestamp(ts)
        file_name = f"frame_{i:02d}_{sec_int:04d}s.jpg"
        out_frame_path = os.path.join(frames_dir, file_name)

        # Extract frame via fast seek (-ss before -i)
        cmd = [
            ffmpeg_bin,
            "-y",
            "-ss", str(ts),
            "-i", video_path,
            "-vframes", "1",
            "-q:v", "2",
            out_frame_path
        ]
        
        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        except Exception:
            continue

        # Find spoken dialogue in transcript around this timestamp (+- 10 seconds)
        context_dialogue = []
        if transcript_segments:
            for seg in transcript_segments:
                start = seg.get("start", 0.0)
                end = seg.get("end", 0.0)
                if (start <= ts <= end) or (abs(start - ts) <= 6.0):
                    text = seg.get("text", "").strip()
                    if text and text not in context_dialogue:
                        context_dialogue.append(text)

        spoken_text = " ".join(context_dialogue).strip()

        frames_info.append({
            "index": i,
            "timestamp": ts,
            "time_str": time_str,
            "file_name": file_name,
            "relative_path": f"frames/{file_name}",
            "absolute_path": os.path.abspath(out_frame_path),
            "spoken_dialogue": spoken_text or "Visual demonstration / music / transition."
        })

    return frames_info
