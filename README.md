# youtube-to-markdown (yt2md)

<p align="right">
  <strong>Language:</strong>
  <a href="README.md">English</a> |
  <a href="README_PT.md">Português (Brasil)</a>
</p>

> 🇧🇷 **Prefere ler em Português?** [Clique aqui para acessar a documentação completa em Português (README_PT.md)](README_PT.md).

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10+-brightgreen.svg)](https://python.org)
[![Whisper: Groq Turbo](https://img.shields.io/badge/Whisper-Groq%20v3%20Turbo-orange.svg)](https://console.groq.com)
[![Harness: Agent--Native](https://img.shields.io/badge/AI%20Harness-Ready-purple.svg)](SKILL.md)
[![Obsidian Canvas](https://img.shields.io/badge/Obsidian-Canvas%20Supported-purple)](https://obsidian.md)
[![Português](https://img.shields.io/badge/Documentação-Português--BR-green)](README_PT.md)

**Universal multimodal reverse-engineering pipeline for AI agents & developers.**  
Turn any YouTube video, playlist, TikTok, Instagram Reel, X/Twitter video, or podcast into structured Markdown, zero-cost native CC or Whisper transcripts, 16-frame visual timelines, public comments, and interactive Obsidian Canvas / Mermaid mind maps.

> **Designed for AI Agent Harnesses:** No GUI, no Streamlit bloat. Built from the ground up to run inside **Claude Code, Antigravity, OpenAI Codex, OpenCode, MiniMax Code, Cursor, and Aider** — or standalone in your terminal.

---

## ⚡ What Makes It Different?

Most YouTube tools only extract raw text transcripts or require bulky web dashboards. **`youtube-to-markdown` is a complete reverse-engineering engine**:

| Capability | Standard Tools | `youtube-to-markdown` |
| :--- | :---: | :---: |
| **Native Captions (CC) First** | ❌ Usually forces paid API | ✅ **Yes ($0 cost, 0.5s speed)** |
| **Neural Whisper Fallback** | ⚠️ Slow local or expensive | ✅ **Groq Whisper v3 Turbo (< 3s)** |
| **Smart Playlist Detection** | ❌ Downloads everything or breaks | ✅ **Interactive prompt (`v=` vs `list=`)** |
| **Audio Optimization** | ❌ Uploads large raw media | ✅ **FFmpeg 16kHz mono 32k (-90% size)** |
| **Visual Timeline (16 Frames)** | ❌ No visual intelligence | ✅ **16 keyframes correlated with dialogue** |
| **Obsidian Canvas Support** | ❌ Plain text only | ✅ **Native `.canvas` JSON + Mermaid `.mmd`** |
| **Public Comments Extraction** | ❌ Requires Google API keys | ✅ **Built-in (Zero API keys needed)** |
| **Agent Harness Compatibility** | ❌ Interactive web GUI only | ✅ **`SKILL.md` + JSON streaming output** |
| **Multi-Platform Ingestion** | ❌ YouTube only | ✅ **YouTube, TikTok, IG, X, Podcasts** |

---

## 📂 Deliverables Generated Per Run

Each processed video creates an organized knowledge hub:

```
output/How to Build an AI Agent - Fireship/
├── INDEX.md                  # Master navigation hub with clickable file:/// links
├── transcript.md             # Full transcript (1-min timestamped chunks + continuous text)
├── video_report.md           # 16-frame visual decupage with spoken context
├── STRATEGIES.md             # Operational SOP, execution playbook & copy-paste prompts
├── MINDMAP.md                # Markdown mind map with embedded Mermaid preview
├── mindmap.canvas            # Native Obsidian visual canvas (color-coded nodes & edges)
├── mindmap.mmd               # Standalone Mermaid diagram file
├── comments.md               # Pinned creator notes, top discussions & community FAQ
├── video_info.json           # Comprehensive structured metadata
└── frames/                   # 16 high-resolution JPEG keyframes
    ├── frame_01_0014s.jpg
    └── ...
```

---

## 📋 Prerequisites & Setup

### 1. Requirements
- **Python 3.10 or higher**
- **FFmpeg** (Recommended: installed on system PATH, or handled automatically via `imageio-ffmpeg`)
- **Groq API Key** (Free tier available at [console.groq.com/keys](https://console.groq.com/keys)) — *only used when video lacks native CC subtitles!*

### 2. Installation

Clone and install dependencies:

```bash
git clone https://github.com/4pixeltechBR/youtube-to-markdown.git
cd youtube-to-markdown
pip install -r requirements.txt
```

*(Optional)* Install locally as a system CLI command:

```bash
pip install -e .
```

### 3. Environment Setup

Copy `.env.example` to `.env` and set your Groq key:

```bash
cp .env.example .env
```

```env
GROQ_API_KEY=gsk_your_groq_api_key_here
# Optional: Default output directory (overrides ./output)
# YT2MD_OUTPUT_DIR=E:/Ideias/
```

---

## 🚀 Usage

### 1. Keyword Search & Discovery (No URL Needed!)
You don't even need to open YouTube or copy links. Search directly from your terminal or AI agent chat:

```bash
# Search top 5 videos on a topic and interactively choose which to process:
yt2md "formas de ganhar dinheiro com IA" -s 5

# Search and batch-process all top 3 results into an intelligence hub:
yt2md "autonomous AI agent architecture" -s 3 --all
```

Interactive Search Menu:
```
======================================================================
  🔍 YouTube Search Results: "formas de ganhar dinheiro com IA"
======================================================================
  [1] 4 FORMAS de GANHAR dinheiro com IA
      Channel: Método VTSD  |  Duration: 18:24  |  Views: 124,500
  [2] 6 Formas de Ganhar Dinheiro com IA Sem Aparecer
      Channel: Nerds de Negócios  |  Duration: 22:15  |  Views: 340,200
----------------------------------------------------------------------
  Options:
  [1-5] Process specific video (recommended)
  [A]   Process ALL in batch (creates comparative search hub)
  [Q]   Quit / Cancel
======================================================================
```

### 2. Interactive URL Mode
Just pass any media URL. If the URL contains both a video and a playlist (`list=` and `v=`), the engine intelligently prompts you:

```bash
python yt2md.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

```
============================================================
  [?] Playlist URL detected with a specific video!
      1) Process ONLY this video (recommended)
      2) Process ENTIRE playlist in batch
============================================================
  Select option [1/2, default: 1]: 1

  Where should files be saved?
  Directory [default: ./output/Rick Astley - Never Gonna Give You Up]:
```

### 2. Batch Processing Playlists
To download an entire playlist into organized subfolders with a master `PLAYLIST_SUMMARY.md`:

```bash
python yt2md.py "https://www.youtube.com/playlist?list=PLxxx" --playlist
```

### 3. Custom Output Directory
Direct files straight into your active project or Obsidian vault:

```bash
python yt2md.py "<URL>" -o "E:/Obsidian/Vault/Research/"
```

### 4. Fast Audio/Text Only (Skip 720p Video & Frames)
For rapid transcription of podcasts or long discussions:

```bash
python yt2md.py "<URL>" --no-frames
```

### 5. Multi-Platform Support
Works seamlessly across all media supported by yt-dlp:
```bash
# TikTok
python yt2md.py "https://www.tiktok.com/@user/video/123456789"

# Instagram Reels
python yt2md.py "https://www.instagram.com/reel/Cxxxxxxx/"

# X (Twitter) Video
python yt2md.py "https://x.com/user/status/123456789"
```

---

## 🤖 Using Inside AI Agent Harnesses

This repository includes a root [`SKILL.md`](SKILL.md) following standard agent harness specifications (Claude Code, Antigravity, OpenAI Codex, OpenCode, Cursor, Aider).

### For AI Coding Agents:
Run with `--json` to receive structured machine-readable responses:

```bash
python yt2md.py "<URL>" --json --single-video
```

**JSON Output Format:**
```json
{
  "status": "success",
  "title": "Autonomous AI Agents in Production",
  "author": "Tech Lead",
  "output_dir": "E:/Ideias/Autonomous AI Agents",
  "index_file": "E:/Ideias/Autonomous AI Agents/INDEX.md",
  "inventory": {
    "Transcript (Markdown)": "E:/.../transcript.md",
    "Visual Timeline Report": "E:/.../video_report.md",
    "Operational SOP & Playbook": "E:/.../STRATEGIES.md",
    "Mind Map (Mermaid View)": "E:/.../MINDMAP.md",
    "Obsidian Interactive Canvas": "E:/.../mindmap.canvas",
    "Community Comments & Insights": "E:/.../comments.md"
  }
}
```

---

## 🧠 Obsidian Canvas Integration

Open the generated folder in your [Obsidian](https://obsidian.md) vault. The `mindmap.canvas` file delivers a native interactive node graph:

```
[ Root Node: Topic ] ───> [ Pillar 1: Context & Problem ] ───> [ Card: Detail ]
                     ───> [ Pillar 2: Architecture ]      ───> [ Card: Detail ]
                     ───> [ Pillar 3: Implementation ]    ───> [ Card: Detail ]
                     ───> [ Pillar 4: Deliverables ]      ───> [ Card: Detail ]
```

---

## 🛠️ CLI Flags Reference

```
usage: yt2md [-h] [-o OUTPUT] [--playlist] [--single-video] [--no-frames]
             [--no-comments] [--force-whisper] [--groq-key GROQ_KEY]
             [--lang LANG] [--json] [-q] [-v] [url]

positional arguments:
  url                   Target media URL (YouTube, Playlist, TikTok, IG, X)

options:
  -h, --help            Show help message and exit
  -o, --output OUTPUT   Custom destination directory
  --playlist            Force batch processing of entire playlist
  --single-video        Force processing only single video in playlist link
  --no-frames           Skip downloading 720p video and 16 visual frames
  --no-comments         Skip public comments extraction
  --force-whisper       Bypass native CC subtitles and force Groq Whisper
  --groq-key KEY        Custom Groq API Key
  --lang LANG           Preferred language codes (default: 'en,pt')
  --json                Output clean JSON to stdout (for AI agents)
  -q, --quiet           Suppress progress banners
  -v, --version         Show program version
```

---

## 📄 License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for more information.

Developed by **4Pixel Tech** ([@4pixeltechBR](https://github.com/4pixeltechBR)).
