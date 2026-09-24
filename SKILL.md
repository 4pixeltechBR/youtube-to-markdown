---
name: youtube-to-markdown
description: Universal multimodal reverse-engineering engine for AI agent harnesses (Claude Code, Antigravity, OpenAI Codex, OpenCode, MiniMax Code, Cursor, Aider). Converts YouTube videos, playlists, TikTok, Instagram, Twitter/X, and podcasts into structured Markdown, native CC/Whisper transcripts, 16-frame visual timelines, comments, and Obsidian Canvas/Mermaid mind maps.
---

# `youtube-to-markdown` Agent Skill

Universal media reverse-engineering engine designed specifically to run inside AI coding agent harnesses. When a developer shares a video link, playlist, or media tutorial, this skill downloads, transcribes, decupages visual keyframes, extracts public feedback, and organizes the intelligence into clean, actionable Markdown and Obsidian Canvas deliverables.

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
python path/to/youtube-to-markdown/yt2md.py "<URL>" --json
```

### Essential CLI Flags for Agent Harnesses

| Flag | Purpose |
| :--- | :--- |
| `--json` | **Required for agents:** Outputs structured JSON to stdout containing output paths and metadata. |
| `--single-video` | Forces processing only the single video (avoids interactive prompts when URL contains `list=`). |
| `--playlist` | Forces batch processing of the entire playlist. |
| `-o <path>` | Specifies exact destination directory (e.g., `-o ./docs/research/`). |
| `--no-frames` | Skips video download and frame extraction (use for pure audio/podcast/speed). |
| `--no-comments` | Skips comment extraction if audience feedback is not needed. |
| `--force-whisper` | Bypasses native CC subtitles and forces Groq Whisper neural transcription. |
| `--lang "en,pt"` | Preferred languages for subtitles and transcription. |

---

## 📦 Deliverables Produced

Each execution produces an organized folder containing:

1. **`INDEX.md`**: Master navigation hub with direct links to all generated files.
2. **`transcript.md`**: Full transcript with 1-minute timestamped checkpoints and continuous text.
3. **`video_report.md`**: Visual timeline featuring 16 equidistant keyframes paired with spoken dialogue.
4. **`STRATEGIES.md`**: Actionable Standard Operating Procedure (SOP), copy-paste prompts, and execution steps.
5. **`MINDMAP.md`**: Concept breakdown with embedded Mermaid mind map.
6. **`mindmap.canvas`**: Native Obsidian Canvas JSON format with color-coded, connected cards.
7. **`comments.md`**: Pinned creator notes, top upvoted community insights, and audience questions.
8. **`video_info.json`**: Complete structured metadata (duration, tags, channel, metrics).
9. **`frames/`**: High-quality JPG keyframe images.

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
   | 🖼️ Visual Timeline (16 Frames) | [video_report.md](file:///path/to/video_report.md) |
   | 📋 Operational SOP | [STRATEGIES.md](file:///path/to/STRATEGIES.md) |
   | 🧠 Obsidian Canvas | [mindmap.canvas](file:///path/to/mindmap.canvas) |
   | 💬 Community Comments | [comments.md](file:///path/to/comments.md) |
   ```
3. **Core Architectural Insights:** 3 to 5 high-signal bullet points summarizing the core methodology.
4. **Next Steps:** Ask the user if they would like to implement the SOP directly into code, scaffold a project, or test the workflow.
