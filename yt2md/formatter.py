"""
yt2md.formatter - Assembles structured intelligence artifacts, SOPs, and reports.
"""

import json
import os
from typing import Dict, List, Optional

from .utils import format_timestamp, to_file_uri


def write_video_info_json(meta: Dict, output_dir: str) -> str:
    """Saves structured video_info.json."""
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "video_info.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    return path


def write_transcript_markdown(
    meta: Dict,
    transcript_data: Dict,
    output_dir: str
) -> str:
    """Renders transcript.md with timestamps and full readable text."""
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "transcript.md")

    title = meta.get("title", "Untitled")
    author = meta.get("author", "Unknown")
    url = meta.get("url", "")
    duration_str = format_timestamp(meta.get("duration", 0))
    source = transcript_data.get("source", "unknown")
    segments = transcript_data.get("segments", [])

    lines = [
        f"# Transcript: {title}\n",
        f"- **Creator / Channel:** {author}",
        f"- **Original URL:** {url}",
        f"- **Duration:** {duration_str}",
        f"- **Extraction Engine:** `{source}`",
        "\n---\n",
        "## ⏱️ Timestamped Transcript\n"
    ]

    # Group segments into ~1-minute blocks for readability
    current_min_block = -1
    for seg in segments:
        start_sec = seg.get("start", 0.0)
        min_mark = int(start_sec // 60)
        time_tag = format_timestamp(start_sec)
        text = seg.get("text", "").strip()

        if min_mark != current_min_block:
            current_min_block = min_mark
            lines.append(f"\n### `[{time_tag}]`\n")

        lines.append(f"**[{time_tag}]** {text}\n")

    lines.append("\n---\n")
    lines.append("## 📜 Continuous Text\n")
    lines.append(transcript_data.get("full_text", "").strip())
    lines.append("\n")

    content = "\n".join(lines)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def write_visual_report_markdown(
    meta: Dict,
    frames: List[Dict],
    output_dir: str
) -> str:
    """Renders video_report.md containing the 16-frame visual decupage."""
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "video_report.md")

    title = meta.get("title", "Untitled")
    lines = [
        f"# Visual Timeline Report: {title}\n",
        "Detailed decupage of 16 equidistant keyframes with spoken dialogue context.\n",
        "---\n"
    ]

    if not frames:
        lines.append("*No visual frames were extracted (audio-only or disabled).*\n")
    else:
        for f in frames:
            idx = f["index"]
            time_str = f["time_str"]
            rel_path = f["relative_path"]
            spoken = f["spoken_dialogue"]

            lines.append(f"## Frame {idx:02d} — `{time_str}`\n")
            lines.append(f"![Frame {idx:02d}]({rel_path})\n")
            lines.append(f"**Dialogue / Context:**\n> \"{spoken}\"\n")
            lines.append("---\n")

    content = "\n".join(lines)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def write_strategies_sop_markdown(
    meta: Dict,
    transcript_text: str,
    output_dir: str
) -> str:
    """
    Renders STRATEGIES.md — the operational SOP and implementation playbook.
    """
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "STRATEGIES.md")

    title = meta.get("title", "Untitled")
    author = meta.get("author", "Unknown")
    url = meta.get("url", "")

    content = f"""# Operational Playbook & SOP: {title}

**Source:** [{title}]({url})  
**Author / Creator:** {author}  
**Format:** Production Standard Operating Procedure (SOP)

---

## 1. Executive Summary & Objective

- **Core Goal:** Extract, operationalize, and replicate the core methodology demonstrated in this material.
- **Target Value:** Eliminate guesswork, accelerate execution, and turn insights into code and automated assets.

---

## 2. Key Architectural Pillars

1. **Pre-flight & Discovery:**
   - Define exact boundaries, dependencies, and environment variables.
   - Verify APIs and required credentials prior to running workflows.

2. **Core Execution Engine:**
   - Follow systematic steps in strict sequence.
   - Prioritize high-signal transformations and lean compute.

3. **Validation & Quality Control:**
   - Inspect output artifacts against requirements.
   - Ensure clean formatting, UTF-8 compatibility, and zero broken links.

---

## 3. Step-by-Step Implementation Guide

### Step 1: Environment Setup
Verify that Python 3.10+ and required packages are configured:
```bash
pip install -r requirements.txt
```

### Step 2: Ingest & Execute
Run the pipeline against your target source:
```bash
python yt2md.py "{url}"
```

### Step 3: Inspect Generated Deliverables
All core assets are saved directly in your designated output directory:
- `transcript.md` — Full transcript with timestamps.
- `video_report.md` — 16-frame visual breakdown.
- `MINDMAP.md` & `mindmap.canvas` — Conceptual hierarchy.
- `comments.md` — Audience feedback and FAQ.

---

## 4. Edge Cases & Red Team Analysis

- **Anti-Bot / Captions Missing:** Native CC is attempted first. If missing, automatically falls back to Groq Whisper v3 Turbo.
- **Large Files (>25MB):** Audio is compressed into 16kHz 32k mono and chunked automatically to prevent API limits.
- **Windows File Paths:** Filenames and paths are sanitized against reserved characters (`<>:"/\\|?*`).

---

*Generated by youtube-to-markdown (4Pixel Tech).*
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def write_master_index_markdown(meta: Dict, file_inventory: Dict[str, str], output_dir: str) -> str:
    """Renders INDEX.md acting as the central hub with clickable links."""
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "INDEX.md")

    title = meta.get("title", "Untitled")
    lines = [
        f"# Knowledge Hub: {title}\n",
        f"- **Original Source:** {meta.get('url', '')}",
        f"- **Creator:** {meta.get('author', 'Unknown')}",
        f"- **Duration:** {format_timestamp(meta.get('duration', 0))}",
        "\n---\n",
        "## 📂 Deliverables Inventory\n",
        "| Artifact | Description | Direct Link |",
        "| :--- | :--- | :--- |"
    ]

    for name, fpath in file_inventory.items():
        if os.path.exists(fpath):
            uri = to_file_uri(fpath)
            basename = os.path.basename(fpath)
            lines.append(f"| **{name}** | `{basename}` | [{basename}]({uri}) |")

    lines.append("\n---\n")
    lines.append("*Generated by youtube-to-markdown — Universal Reverse-Engineering Pipeline.*\n")

    content = "\n".join(lines)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path
