"""
yt2md.visual - Smart Perceptual Visual Timeline Extractor (v1.2.0).

Implements a two-stage computer vision pipeline for tutorial and lecture decupage:
1. Stage 1 (RAM Stream Analysis): Streams 1 FPS via FFmpeg pipe with an 80% central
   Region-of-Interest (ROI) crop (ignoring corner webcams and OS taskbars) in 64x64 grayscale.
   Computes 256-bit Difference Hash (dHash 16x16, compatible with imagehash) and Sobel/Laplacian
   high-frequency edge density (distinguishing code/diagrams/slides from talking-head B-roll).
2. Stage 2 (Dwell-Time Stabilization & HD Capture): Groups frames into stable visual plateaus,
   ignores mid-scroll/transition blurs, selects the sharpest stabilized timestamp per scene,
   and extracts high-definition 720p JPEGs correlated with the full scene dialogue window.
"""

import math
import os
import subprocess
from typing import Dict, List, Optional, Tuple

from .utils import format_timestamp, get_ffmpeg_binary

# Optional external imagehash + Pillow acceleration (with deterministic built-in 256-bit fallback)
try:
    import imagehash  # type: ignore
    from PIL import Image  # type: ignore
    HAS_IMAGEHASH = True
except ImportError:
    HAS_IMAGEHASH = False


def compute_frame_metrics_64x64(buf: bytes) -> Tuple[int, float, float, float]:
    """
    Given a raw 64x64 grayscale frame buffer (4096 bytes), computes:
    - dhash_256: 256-bit perceptual difference hash (17x16 horizontal gradient comparison)
    - edge_density: Mean horizontal + vertical gradient magnitude (high for code/slides/text)
    - mean_luma: Mean brightness (0..255) to reject black fade frames
    - std_luma: Brightness standard deviation to reject flat/solid-color transition frames
    """
    if len(buf) < 4096:
        return 0, 0.0, 0.0, 0.0

    # 1. Mean and standard deviation of luminance (sampled on 16x16 stride-4 grid for speed)
    samples = [buf[(y * 4) * 64 + (x * 4)] for y in range(16) for x in range(16)]
    mean_luma = sum(samples) / 256.0
    variance = sum((px - mean_luma) ** 2 for px in samples) / 256.0
    std_luma = math.sqrt(variance)

    # 2. High-frequency edge density (Manhattan gradient over inner 60x60 grid, stride 2)
    grad_sum = 0
    grad_count = 0
    for y in range(2, 62, 2):
        row_off = y * 64
        next_row_off = (y + 1) * 64
        for x in range(2, 62, 2):
            p = buf[row_off + x]
            gx = abs(buf[row_off + x + 1] - p)
            gy = abs(buf[next_row_off + x] - p)
            grad_sum += gx + gy
            grad_count += 1
    edge_density = grad_sum / float(max(1, grad_count))

    # 3. 256-bit dHash (17 columns x 16 rows)
    if HAS_IMAGEHASH:
        try:
            img = Image.frombytes("L", (64, 64), buf)
            dh = imagehash.dhash(img, hash_size=16)
            dhash_int = int(str(dh), 16)
            return dhash_int, edge_density, mean_luma, std_luma
        except Exception:
            pass

    # Deterministic built-in 256-bit dHash (downsamples 64x64 -> 17x16 via area averaging)
    dhash_int = 0
    bit_idx = 0
    for row in range(16):
        y0 = row * 4
        prev_val = 0.0
        for col in range(17):
            x0 = int(col * 64 / 17)
            x1 = max(x0 + 1, int((col + 1) * 64 / 17))
            # Average 4x(x1-x0) block
            block_sum = 0
            block_cnt = 0
            for yy in range(y0, min(64, y0 + 4)):
                r_off = yy * 64
                for xx in range(x0, min(64, x1)):
                    block_sum += buf[r_off + xx]
                    block_cnt += 1
            cur_val = block_sum / float(max(1, block_cnt))
            if col > 0:
                if cur_val > prev_val:
                    dhash_int |= (1 << bit_idx)
                bit_idx += 1
            prev_val = cur_val

    return dhash_int, edge_density, mean_luma, std_luma


def hamming_distance(h1: int, h2: int) -> int:
    """Computes bit-level Hamming distance between two 256-bit perceptual hashes."""
    return (h1 ^ h2).bit_count()


def classify_visual_density(edge_density: float) -> str:
    """Classifies screen content type based on high-frequency spatial edge energy."""
    if edge_density >= 14.0:
        return "Alta Densidade (Código / Diagrama / Terminal)"
    if edge_density >= 7.5:
        return "Média Densidade (Slide / Interface / Browser)"
    return "Baixa Densidade (Apresentador / Transição / B-Roll)"


def _collect_dialogue_for_window(
    transcript_segments: Optional[List[Dict]],
    start_ts: float,
    end_ts: float,
    fallback_pad: float = 5.0
) -> str:
    """Gathers spoken transcript segments overlapping the active scene interval [start_ts, end_ts]."""
    if not transcript_segments:
        return "Visual demonstration / music / transition."

    win_start = max(0.0, start_ts - 1.5)
    win_end = max(win_start + fallback_pad, end_ts + 1.5)

    context_dialogue = []
    for seg in transcript_segments:
        s_start = seg.get("start", 0.0)
        s_end = seg.get("end", s_start)
        # Check overlap with [win_start, win_end]
        if (s_end >= win_start and s_start <= win_end) or abs(s_start - start_ts) <= fallback_pad:
            text = seg.get("text", "").strip()
            if text and text not in context_dialogue:
                context_dialogue.append(text)

    spoken = " ".join(context_dialogue).strip()
    if len(spoken) > 900:
        spoken = spoken[:897].rsplit(" ", 1)[0] + "..."
    return spoken or "Visual demonstration / music / transition."


def _scan_video_perceptual_scenes(
    video_path: str,
    ffmpeg_bin: str,
    duration: float,
    hash_threshold: int = 26,
    min_dwell: int = 2,
    max_frames: int = 36
) -> List[Dict]:
    """
    Streams video at 1 FPS (or 0.5 FPS for very long videos > 90 min) with an 80% central ROI crop
    directly into memory, detecting stable perceptual scenes via 256-bit dHash and edge density.
    """
    # Adaptive sampling rate: 1.0 FPS for videos up to 90 min, 0.5 FPS for > 90 min
    sample_fps = 1.0 if duration <= 5400 else 0.5
    dt = 1.0 / sample_fps

    # Central 80% ROI crop ignores corner webcams (PIP) and OS taskbars
    vf_chain = f"fps={sample_fps},crop=iw*0.80:ih*0.80:iw*0.10:ih*0.10,scale=64:64:flags=area"
    cmd = [
        ffmpeg_bin,
        "-v", "error",
        "-i", video_path,
        "-vf", vf_chain,
        "-f", "rawvideo",
        "-pix_fmt", "gray",
        "pipe:1"
    ]

    raw_frames: List[Dict] = []
    frame_bytes = 64 * 64  # 4096 bytes per frame

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    try:
        idx = 0
        while True:
            chunk = proc.stdout.read(frame_bytes) if proc.stdout else b""
            if not chunk or len(chunk) < frame_bytes:
                break
            ts = round(idx * dt, 2)
            dhash, edge_dens, mean_luma, std_luma = compute_frame_metrics_64x64(chunk)
            raw_frames.append({
                "sec_idx": idx,
                "timestamp": ts,
                "dhash": dhash,
                "edge_density": edge_dens,
                "mean_luma": mean_luma,
                "std_luma": std_luma,
                "valid": (mean_luma > 7.0 and mean_luma < 250.0 and std_luma > 3.5)
            })
            idx += 1
    finally:
        if proc.stdout:
            proc.stdout.close()
        proc.wait()

    if not raw_frames:
        return []

    # Adjust min_dwell for short videos (< 60s)
    effective_min_dwell = 1 if duration < 75 else max(1, int(round(min_dwell * sample_fps)))

    # Segment into stable visual plateaus
    plateaus: List[List[Dict]] = []
    current_group: List[Dict] = []
    anchor_hash: Optional[int] = None

    for rf in raw_frames:
        if not rf["valid"]:
            continue
        if anchor_hash is None:
            current_group = [rf]
            anchor_hash = rf["dhash"]
            continue

        dist = hamming_distance(rf["dhash"], anchor_hash)
        # Also check instant frame-to-frame jump to catch gradual scrolls that accumulate
        prev_dist = hamming_distance(rf["dhash"], current_group[-1]["dhash"])

        if dist <= hash_threshold and prev_dist <= int(hash_threshold * 0.85):
            current_group.append(rf)
        else:
            if len(current_group) >= effective_min_dwell:
                plateaus.append(current_group)
            current_group = [rf]
            anchor_hash = rf["dhash"]

    if len(current_group) >= effective_min_dwell:
        plateaus.append(current_group)

    # Fallback if video was extreme fast-cut and no plateau met min_dwell
    if not plateaus and raw_frames:
        step = max(1, len(raw_frames) // min(16, len(raw_frames)))
        plateaus = [[raw_frames[i]] for i in range(0, len(raw_frames), step)]

    # Build scene candidates with stabilization (pick sharpest settled frame inside each plateau)
    scenes: List[Dict] = []
    for plat in plateaus:
        start_ts = plat[0]["timestamp"]
        end_ts = round(plat[-1]["timestamp"] + dt, 2)
        dwell_sec = max(dt, round(end_ts - start_ts, 1))

        # Skip first frame of plateau if >= 3 frames to avoid fade-in / scroll arrival blur
        inner_candidates = plat[1:-1] if len(plat) >= 4 else (plat[1:] if len(plat) >= 2 else plat)
        best_frame = max(inner_candidates, key=lambda x: x["edge_density"])

        scenes.append({
            "timestamp": best_frame["timestamp"],
            "start_ts": start_ts,
            "end_ts": end_ts,
            "dwell_sec": dwell_sec,
            "dhash": best_frame["dhash"],
            "edge_density": round(best_frame["edge_density"], 2),
            "visual_type": classify_visual_density(best_frame["edge_density"])
        })

    # Cross-scene deduplication: suppress A -> B (webcam) -> A (identical code screen) within 90s
    deduped_scenes: List[Dict] = []
    for sc in scenes:
        is_dup = False
        for prev in reversed(deduped_scenes[-4:]):
            h_dist = hamming_distance(sc["dhash"], prev["dhash"])
            time_gap = sc["start_ts"] - prev["end_ts"]
            # If practically the exact same screen (< 14 bits out of 256) within 90s
            if h_dist <= max(10, hash_threshold // 2) and time_gap < 90.0:
                prev["end_ts"] = sc["end_ts"]
                prev["dwell_sec"] = round(prev["dwell_sec"] + sc["dwell_sec"], 1)
                if sc["edge_density"] > prev["edge_density"]:
                    prev["timestamp"] = sc["timestamp"]
                    prev["edge_density"] = sc["edge_density"]
                    prev["visual_type"] = sc["visual_type"]
                is_dup = True
                break
        if not is_dup:
            deduped_scenes.append(sc)

    # Budget pruning: if scenes exceed max_frames, prioritize by Dwell Time x Information Density
    if max_frames > 0 and len(deduped_scenes) > max_frames:
        for sc in deduped_scenes:
            # Score rewards longer screen dwell time and high code/diagram edge density
            dwell_weight = math.log2(1.0 + max(1.0, sc["dwell_sec"]))
            edge_weight = 1.0 + min(2.0, sc["edge_density"] / 12.0)
            sc["_score"] = dwell_weight * edge_weight

        # Keep top max_frames by importance score, then re-sort chronologically
        top_scenes = sorted(deduped_scenes, key=lambda x: x["_score"], reverse=True)[:max_frames]
        deduped_scenes = sorted(top_scenes, key=lambda x: x["timestamp"])

    return deduped_scenes


def extract_uniform_timeline(
    video_path: str,
    duration: float,
    output_dir: str,
    num_frames: int = 16,
    transcript_segments: Optional[List[Dict]] = None
) -> List[Dict]:
    """
    Legacy uniform equidistant keyframe extraction (Time-Based Sampling).
    """
    ffmpeg_bin = get_ffmpeg_binary()
    if not ffmpeg_bin:
        raise RuntimeError("FFmpeg executable not found. Cannot extract visual frames.")

    frames_dir = os.path.join(output_dir, "frames")
    os.makedirs(frames_dir, exist_ok=True)

    if duration <= 0:
        duration = 60.0

    step = duration / (num_frames + 1)
    frames_info = []

    for i in range(1, num_frames + 1):
        ts = round(i * step, 2)
        sec_int = int(ts)
        time_str = format_timestamp(ts)
        file_name = f"frame_{i:02d}_{sec_int:04d}s.jpg"
        out_frame_path = os.path.join(frames_dir, file_name)

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

        spoken_text = _collect_dialogue_for_window(
            transcript_segments,
            start_ts=max(0.0, ts - 5.0),
            end_ts=ts + 5.0
        )

        frames_info.append({
            "index": i,
            "timestamp": ts,
            "time_str": time_str,
            "start_time_str": format_timestamp(max(0.0, ts - step / 2)),
            "end_time_str": format_timestamp(min(duration, ts + step / 2)),
            "dwell_sec": round(step, 1),
            "visual_type": "Amostragem Uniforme",
            "edge_density": 0.0,
            "file_name": file_name,
            "relative_path": f"frames/{file_name}",
            "absolute_path": os.path.abspath(out_frame_path),
            "spoken_dialogue": spoken_text
        })

    return frames_info


def extract_visual_timeline(
    video_path: str,
    duration: float,
    output_dir: str,
    num_frames: int = 36,
    transcript_segments: Optional[List[Dict]] = None,
    mode: str = "smart",
    hash_threshold: int = 26,
    min_dwell: int = 2
) -> List[Dict]:
    """
    Extracts visual keyframes across the media duration.
    - mode="smart" (default): Content-aware perceptual deduplication (256-bit dHash + 80% ROI crop
      + Dwell-time plateau stabilization + Edge density scoring).
    - mode="uniform": Fixed equidistant sampling across duration.
    """
    ffmpeg_bin = get_ffmpeg_binary()
    if not ffmpeg_bin:
        raise RuntimeError("FFmpeg executable not found. Cannot extract visual frames.")

    if mode == "uniform":
        return extract_uniform_timeline(
            video_path=video_path,
            duration=duration,
            output_dir=output_dir,
            num_frames=num_frames,
            transcript_segments=transcript_segments
        )

    frames_dir = os.path.join(output_dir, "frames")
    os.makedirs(frames_dir, exist_ok=True)

    # Clear stale frames from previous runs in the same folder
    for existing in os.listdir(frames_dir):
        if existing.startswith("frame_") and existing.endswith(".jpg"):
            try:
                os.remove(os.path.join(frames_dir, existing))
            except OSError:
                pass

    if duration <= 0:
        duration = 60.0

    scenes = _scan_video_perceptual_scenes(
        video_path=video_path,
        ffmpeg_bin=ffmpeg_bin,
        duration=duration,
        hash_threshold=hash_threshold,
        min_dwell=min_dwell,
        max_frames=num_frames
    )

    if not scenes:
        return extract_uniform_timeline(
            video_path=video_path,
            duration=duration,
            output_dir=output_dir,
            num_frames=min(16, num_frames),
            transcript_segments=transcript_segments
        )

    frames_info: List[Dict] = []
    for i, sc in enumerate(scenes, start=1):
        ts = sc["timestamp"]
        sec_int = int(ts)
        time_str = format_timestamp(ts)
        start_str = format_timestamp(sc["start_ts"])
        end_str = format_timestamp(sc["end_ts"])
        file_name = f"frame_{i:02d}_{sec_int:04d}s.jpg"
        out_frame_path = os.path.join(frames_dir, file_name)

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

        spoken_text = _collect_dialogue_for_window(
            transcript_segments,
            start_ts=sc["start_ts"],
            end_ts=sc["end_ts"]
        )

        frames_info.append({
            "index": i,
            "timestamp": ts,
            "time_str": time_str,
            "start_ts": sc["start_ts"],
            "end_ts": sc["end_ts"],
            "start_time_str": start_str,
            "end_time_str": end_str,
            "dwell_sec": sc["dwell_sec"],
            "visual_type": sc["visual_type"],
            "edge_density": sc["edge_density"],
            "file_name": file_name,
            "relative_path": f"frames/{file_name}",
            "absolute_path": os.path.abspath(out_frame_path),
            "spoken_dialogue": spoken_text
        })

    return frames_info
