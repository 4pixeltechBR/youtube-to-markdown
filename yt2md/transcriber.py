"""
yt2md.transcriber - Neural audio transcription via Groq Whisper v3 Turbo.
Handles audio compression (16kHz mono 32k) and automatic chunking for long media.
"""

import json
import math
import os
import subprocess
from typing import Dict, List, Optional

from .utils import get_ffmpeg_binary


def compress_audio(input_audio_path: str, output_mp3_path: str) -> str:
    """
    Compresses audio into Whisper-optimized format:
    16kHz sampling rate, mono channel, 32kbps bitrate.
    Reduces file size by up to 90% while preserving speech clarity.
    """
    ffmpeg_bin = get_ffmpeg_binary()
    if not ffmpeg_bin:
        raise RuntimeError("FFmpeg executable not found. Install FFmpeg or pip install imageio-ffmpeg.")

    cmd = [
        ffmpeg_bin,
        "-y",
        "-i", input_audio_path,
        "-ar", "16000",
        "-ac", "1",
        "-b:a", "32k",
        output_mp3_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return output_mp3_path


def split_audio_into_chunks(audio_path: str, chunk_duration_sec: int = 1200) -> List[str]:
    """
    Splits long audio files into smaller chunks (default 20 minutes)
    to strictly adhere to API file size limits (< 25MB).
    """
    ffmpeg_bin = get_ffmpeg_binary()
    if not ffmpeg_bin:
        raise RuntimeError("FFmpeg executable not found.")

    output_pattern = audio_path.replace(".mp3", "_chunk_%03d.mp3")
    cmd = [
        ffmpeg_bin,
        "-y",
        "-i", audio_path,
        "-f", "segment",
        "-segment_time", str(chunk_duration_sec),
        "-c", "copy",
        output_pattern
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    base_dir = os.path.dirname(audio_path)
    base_name = os.path.basename(audio_path).replace(".mp3", "_chunk_")
    chunks = sorted([
        os.path.join(base_dir, f)
        for f in os.listdir(base_dir)
        if f.startswith(base_name) and f.endswith(".mp3")
    ])
    return chunks if chunks else [audio_path]


def transcribe_with_groq(
    audio_path: str,
    api_key: Optional[str] = None,
    language: Optional[str] = None,
    output_dir: Optional[str] = None
) -> Dict:
    """
    Transcribes audio using Groq's whisper-large-v3-turbo API.
    Returns structured segments and full transcript text.
    """
    api_key = api_key or os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY is not set. Export it in your environment or add it to a .env file.\n"
            "Get a free API key at: https://console.groq.com/keys"
        )

    try:
        from groq import Groq
    except ImportError:
        raise ImportError("groq package is required for neural transcription. Install with: pip install groq")

    client = Groq(api_key=api_key)

    # Check file size (Groq limit is 25MB)
    file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
    chunks_to_process = [audio_path]
    is_chunked = False

    if file_size_mb > 24:
        is_chunked = True
        chunks_to_process = split_audio_into_chunks(audio_path, chunk_duration_sec=1200)

    all_segments: List[Dict] = []
    full_text_parts: List[str] = []
    time_offset = 0.0

    for chunk in chunks_to_process:
        with open(chunk, "rb") as file:
            kwargs = {
                "file": file,
                "model": "whisper-large-v3-turbo",
                "response_format": "verbose_json",
            }
            if language:
                kwargs["language"] = language

            response = client.audio.transcriptions.create(**kwargs)

        # Process segments with offset
        chunk_segments = getattr(response, "segments", []) or []
        for seg in chunk_segments:
            seg_dict = seg if isinstance(seg, dict) else seg.model_dump()
            all_segments.append({
                "start": round(seg_dict.get("start", 0.0) + time_offset, 2),
                "end": round(seg_dict.get("end", 0.0) + time_offset, 2),
                "text": seg_dict.get("text", "").strip()
            })

        chunk_text = getattr(response, "text", "") or ""
        if chunk_text:
            full_text_parts.append(chunk_text.strip())

        # Calculate chunk offset
        if is_chunked and chunk_segments:
            last_seg = chunk_segments[-1]
            last_end = last_seg.get("end", 0.0) if isinstance(last_seg, dict) else getattr(last_seg, "end", 0.0)
            time_offset += last_end

        # Clean up temporary chunk files if chunked
        if is_chunked and chunk != audio_path and os.path.exists(chunk):
            try:
                os.remove(chunk)
            except OSError:
                pass

    full_text = " ".join(full_text_parts).strip()

    result = {
        "source": "groq_whisper_v3_turbo",
        "model": "whisper-large-v3-turbo",
        "segments": all_segments,
        "full_text": full_text
    }

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        json_path = os.path.join(output_dir, "transcript.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

    return result
