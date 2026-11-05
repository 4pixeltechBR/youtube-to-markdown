---
name: youtube-to-markdown
description: Universal multimodal reverse-engineering engine (v1.2.0) for AI agent harnesses (Claude Code, Antigravity, OpenAI Codex, OpenCode, MiniMax Code, Cursor, Aider). Converts YouTube videos, playlists, TikTok, Instagram, Twitter/X, and podcasts into structured Markdown, native CC/Whisper transcripts, Smart Perceptual Keyframes (256-bit dHash + 80% ROI + Dwell Stabilization), comments, and Obsidian Canvas/Mermaid mind maps.
---

# `youtube-to-markdown` Agent Skill (v1.2.0)

Universal media reverse-engineering engine designed specifically to run inside AI coding agent harnesses. When a developer shares a video link, playlist, or media tutorial, this skill downloads, transcribes, decupages **Smart Perceptual Keyframes** (using 1-FPS stream scanning, 256-bit `dHash`, 80% central ROI crop to ignore corner webcams, and dwell-time plateau stabilization), extracts public feedback, and organizes the intelligence into clean, actionable Markdown and Obsidian Canvas deliverables.

---

## 🛠️ When to Activate

Use this skill whenever:
1. The user provides a YouTube URL, playlist, TikTok, Instagram Reel, X/Twitter video, or podcast and asks to:
   - "Download / summarize / extract / reverse-engineer this video"
   - "Transcribe this media"
   - "Extract the SOP or playbook from this tutorial"
   - "Break down the architecture shown in this video"
   - "Extract the visual frames and slides from this tech talk"
   - "Analyze what viewers are asking in the comments"
2. The user wants to build a project inspired by an online video or lecture.
3. The user needs an Obsidian Canvas or Mermaid mind map representing video concepts.

---

## 🚀 Execution Command for Agents

Run the tool using your bash/terminal execution tool with `--json` for machine-readable output:

```bash
python -m yt2md "<URL>" --json
```

Or execute directly via the root script:

```bash
python E:/Ideias/youtube-to-markdown/yt2md.py "<URL>" --json
```

### Essential CLI Flags for Agent Harnesses

| Flag | Purpose |
| :--- | :--- |
| `--json` | **Required for agents:** Outputs structured JSON to stdout containing output paths and metadata. |
| `--frame-mode {smart,uniform}` | Visual engine: `smart` (default: 256-bit dHash + 80% ROI + Dwell Stabilization) or `uniform` (equidistant). |
| `--frames <N>` | Max unique perceptual keyframes to extract (default: **36**; set `0` for unlimited unique screens). |
| `--min-dwell <sec>` | Minimum seconds a screen must remain stable to be captured in smart mode (default: **2**). |
| `--hash-threshold <bits>` | Hamming distance threshold out of 256 bits to trigger a new visual scene (default: **26**). |
| `-s <N>`, `--search <N>` | Searches YouTube by keywords and returns/processes top N results (e.g. `-s 5`). |
| `--all` | Processes all search results or playlist entries in batch. |
| `--pick <N>` | Directly selects search result index N (1-based) without interactive prompting. |
| `--single-video` | Forces processing only the single video (avoids interactive prompts when URL contains `list=`). |
| `--playlist` | Forces batch processing of the entire playlist. |
| `-o <path>` | Specifies exact destination directory (e.g., `-o "E:/Ideias/Nome - Autor"`). |
| `--no-frames` | Skips video download and frame extraction (use for pure audio/podcast/speed). |
| `--no-comments` | Skips comment extraction if audience feedback is not needed. |
| `--force-whisper` | Bypasses native CC subtitles and forces Groq Whisper neural transcription. |
| `--lang "en,pt"` | Preferred languages for subtitles and transcription. |

### Search Invocation Example for Agents
```bash
# Agent discovers top video on a topic and ingests automatically:
python E:/Ideias/youtube-to-markdown/yt2md.py "formas de ganhar dinheiro com IA" --json --pick 1
```

---

## 🧠 Smart Perceptual Keyframe Engine (v1.2.0)

Instead of blind uniform time slicing (`duration / N`), `yt2md` v1.2.0 uses a 2-stage computer vision pipeline:
1. **RAM Pipe Stream (`1 FPS` + `80% Central ROI Crop`):** Scans the video in memory without disk thrashing, cropping out the outer 10% borders (ignoring Picture-in-Picture webcams and OS taskbars).
2. **256-bit `dHash` (`16x16`) + Edge Density:** Detects even subtle code/tab switches inside dark IDEs (VS Code) while computing spatial gradient density to distinguish code/diagrams/slides from low-density talking-head B-roll.
3. **Dwell-Time Stabilization:** Waits for scroll/transition animations to settle (`>= 2s` plateau) and captures the sharpest frame inside the plateau, annotating the exact `[start -> end]` dwell duration and full scene dialogue in `video_report.md`.

---

## 📦 Deliverables Produced

Each execution produces an organized folder containing:

1. **`INDEX.md`**: Master navigation hub with direct links to all generated files.
2. **`transcript.md`**: Full transcript with 1-minute timestamped checkpoints and continuous text.
3. **`video_report.md`**: Smart Perceptual Visual Timeline featuring unique stabilized keyframes, screen dwell duration (`start -> end`), visual density classification, and paired spoken dialogue.
4. **`STRATEGIES.md`**: Actionable Standard Operating Procedure (SOP), copy-paste prompts, and execution steps.
5. **`MINDMAP.md`**: Concept breakdown with embedded Mermaid mind map.
6. **`mindmap.canvas`**: Native Obsidian Canvas JSON format with color-coded, connected cards.
7. **`comments.md`**: Pinned creator notes, top upvoted community insights, and audience questions.
8. **`video_info.json`**: Complete structured metadata (duration, tags, channel, metrics).
9. **`frames/`**: High-quality 720p JPG keyframe images for every unique stabilized visual scene.

---

## 💡 Agent Response Protocol

After executing `yt2md`, present the results to the user following this format:

1. **Title & Creator:** Clean headline with video author, duration, and extraction source (Native CC vs Whisper).
2. **Deliverables Table:** Clickable local file links:
   ```markdown
   | Artifact | Link |
   | :--- | :--- |
   | 🧭 Master Index | [INDEX.md](file:///path/to/INDEX.md) |
   | 📜 Transcript | [transcript.md](file:///path/to/transcript.md) |
   | 🖼️ Smart Visual Timeline | [video_report.md](file:///path/to/video_report.md) |
   | 📋 Operational SOP | [STRATEGIES.md](file:///path/to/STRATEGIES.md) |
   | 🧠 Obsidian Canvas | [mindmap.canvas](file:///path/to/mindmap.canvas) |
   | 💬 Community Comments | [comments.md](file:///path/to/comments.md) |
   ```
3. **Core Architectural Insights:** 3 to 5 high-signal bullet points summarizing the core methodology.
4. **Next Steps:** Ask the user if they would like to implement the SOP directly into code, scaffold a project, or test the workflow.
