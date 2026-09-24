"""
yt2md.extractor - Core media extractor, playlist intelligence, and pipeline orchestrator.
"""

import os
import sys
from typing import Dict, List, Optional
from urllib.parse import parse_qs, urlparse

import yt_dlp

from .comments import extract_comments_data, format_comments_markdown
from .formatter import (
    write_master_index_markdown,
    write_strategies_sop_markdown,
    write_transcript_markdown,
    write_video_info_json,
    write_visual_report_markdown,
)
from .mindmap import build_mindmap_assets
from .subtitles import extract_native_subtitles
from .transcriber import compress_audio, transcribe_with_groq
from .utils import ensure_utf8_io, format_timestamp, sanitize_filename, to_file_uri
from .visual import extract_visual_timeline


def is_interactive() -> bool:
    """Checks whether the current process is running in an interactive terminal."""
    return sys.stdin.isatty() and sys.stdout.isatty()


def detect_playlist_intent(url: str, force_playlist: bool = False, force_single: bool = False) -> str:
    """
    Analyzes URL to detect if it's a playlist or a video embedded in a playlist.
    Returns: 'single' or 'playlist'.
    """
    if force_single:
        return "single"
    if force_playlist:
        return "playlist"

    parsed = urlparse(url)
    qs = parse_qs(parsed.query)

    has_video = "v" in qs or "youtu.be" in parsed.netloc
    has_playlist = "list" in qs or "/playlist" in parsed.path

    # If it has both video and playlist ID
    if has_video and has_playlist:
        if is_interactive():
            print("\n" + "=" * 60)
            print("  [?] Playlist URL detected with a specific video!")
            print("      1) Process ONLY this video (recommended)")
            print("      2) Process ENTIRE playlist in batch")
            print("=" * 60)
            try:
                choice = input("  Select option [1/2, default: 1]: ").strip()
                if choice == "2":
                    return "playlist"
            except (EOFError, KeyboardInterrupt):
                pass
        # Default in headless/agent mode or default choice is single video
        return "single"

    # If it is purely a playlist
    if has_playlist and not has_video:
        return "playlist"

    return "single"


def resolve_output_dir(
    custom_dir: Optional[str],
    default_name: str,
    base_dir: Optional[str] = None
) -> str:
    """
    Resolves the final output directory based on priority:
    1. CLI argument `--output`
    2. Environment variable `YT2MD_OUTPUT_DIR`
    3. Interactive terminal prompt (if interactive)
    4. Default: `./output/<default_name>`
    """
    if custom_dir:
        return os.path.abspath(custom_dir)

    env_dir = os.getenv("YT2MD_OUTPUT_DIR")
    if env_dir:
        return os.path.abspath(os.path.join(env_dir, sanitize_filename(default_name)))

    suggested = os.path.abspath(os.path.join(".", "output", sanitize_filename(default_name)))

    if is_interactive() and not os.getenv("YT2MD_NON_INTERACTIVE"):
        print(f"\n  Where should files be saved?")
        try:
            val = input(f"  Directory [default: {suggested}]: ").strip()
            if val:
                return os.path.abspath(val)
        except (EOFError, KeyboardInterrupt):
            pass

    return suggested


def process_single_video(
    url: str,
    output_dir: Optional[str] = None,
    extract_frames: bool = True,
    extract_comments: bool = True,
    force_whisper: bool = False,
    groq_api_key: Optional[str] = None,
    preferred_lang: str = "en,pt",
    quiet: bool = False
) -> Dict:
    """
    Executes the full multimodal reverse-engineering pipeline for a single media item.
    """
    ensure_utf8_io()

    # Clean URL if single video was requested from a playlist link
    if "list=" in url and "v=" in url:
        parsed = urlparse(url)
        qs = parse_qs(parsed.query)
        video_id = qs.get("v", [None])[0]
        if video_id:
            url = f"https://www.youtube.com/watch?v={video_id}"

    if not quiet:
        print(f"\n[>] Ingesting media: {url}")

    # Step 0: Extract Metadata
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "getcomments": extract_comments,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    title = info.get("title") or "Untitled Media"
    author = info.get("uploader") or info.get("channel") or "Unknown"
    duration = float(info.get("duration") or 0.0)

    # Resolve output directory
    folder_name = f"{title} - {author}"
    out_dir = resolve_output_dir(output_dir, folder_name)
    os.makedirs(out_dir, exist_ok=True)

    if not quiet:
        print(f"[*] Title: {title}")
        print(f"[*] Author: {author} | Duration: {format_timestamp(duration)}")
        print(f"[*] Destination: {out_dir}")

    meta = {
        "title": title,
        "author": author,
        "url": url,
        "duration": duration,
        "description": info.get("description", ""),
        "upload_date": info.get("upload_date", ""),
        "view_count": info.get("view_count", 0),
        "tags": info.get("tags", []),
        "output_dir": out_dir
    }

    # Step 1: Subtitle check (Native CC first: $0, 0.5s)
    langs_tuple = tuple(l.strip() for l in preferred_lang.split(","))
    transcript_data = None

    if not force_whisper:
        if not quiet:
            print("[*] Checking for native captions (CC)...")
        transcript_data = extract_native_subtitles(info, preferred_langs=langs_tuple, output_dir=out_dir)
        if transcript_data and not quiet:
            lang_label = transcript_data.get("language", "unknown")
            is_auto = "auto-generated" if transcript_data.get("is_auto") else "official"
            print(f"[+] Found native CC ({lang_label}, {is_auto})! Skipping neural transcription ($0 cost).")

    # Step 2: Fallback to Groq Whisper v3 Turbo if captions not available
    if not transcript_data:
        if not quiet:
            print("[!] Native CC unavailable. Downloading speech audio for Groq Whisper v3 Turbo...")

        temp_audio = os.path.join(out_dir, "temp_audio.m4a")
        compressed_mp3 = os.path.join(out_dir, "audio.mp3")

        audio_dl_opts = {
            "format": "bestaudio/best",
            "outtmpl": temp_audio,
            "quiet": True,
            "no_warnings": True,
            "overwrites": True
        }
        with yt_dlp.YoutubeDL(audio_dl_opts) as ydl:
            ydl.download([url])

        if not quiet:
            print("[*] Compressing audio (16kHz mono 32k) for high-speed transcription...")
        compress_audio(temp_audio, compressed_mp3)

        # Cleanup raw audio
        if os.path.exists(temp_audio):
            try:
                os.remove(temp_audio)
            except OSError:
                pass

        if not quiet:
            print("[*] Transcribing via Groq (whisper-large-v3-turbo)...")
        transcript_data = transcribe_with_groq(
            compressed_mp3,
            api_key=groq_api_key,
            language=langs_tuple[0] if langs_tuple else None,
            output_dir=out_dir
        )
        if not quiet:
            print("[+] Neural transcription complete!")

    meta["transcript_source"] = transcript_data.get("source", "unknown")

    # Step 3: Visual Timeline (16 frames)
    frames = []
    if extract_frames and duration > 5:
        if not quiet:
            print("[*] Downloading video stream (720p) for 16-frame visual timeline...")
        video_file = os.path.join(out_dir, "video.mp4")
        video_dl_opts = {
            "format": "bestvideo[height<=720]+bestaudio/best[height<=720]/best",
            "outtmpl": video_file,
            "quiet": True,
            "no_warnings": True,
            "overwrites": True
        }
        try:
            with yt_dlp.YoutubeDL(video_dl_opts) as ydl:
                ydl.download([url])

            if not quiet:
                print("[*] Extracting 16 equidistant keyframes with dialogue correlation...")
            frames = extract_visual_timeline(
                video_file,
                duration=duration,
                output_dir=out_dir,
                num_frames=16,
                transcript_segments=transcript_data.get("segments")
            )
            if not quiet:
                print(f"[+] Extracted {len(frames)} visual frames.")
        except Exception as e:
            if not quiet:
                print(f"[-] Video frame extraction skipped: {e}")

    # Step 4: Comments Extraction
    comments_file = None
    if extract_comments:
        if not quiet:
            print("[*] Processing public comments & community insights...")
        comments_data = extract_comments_data(info, max_comments=50, output_dir=out_dir)
        comments_md_text = format_comments_markdown(comments_data)
        comments_file = os.path.join(out_dir, "comments.md")
        with open(comments_file, "w", encoding="utf-8") as f:
            f.write(comments_md_text)

    # Step 5: Dual Mind Maps (Mermaid & Obsidian Canvas)
    if not quiet:
        print("[*] Synthesizing Mermaid diagram and native Obsidian Canvas (.canvas)...")
    mindmaps = build_mindmap_assets(
        title=title,
        summary_text=info.get("description", ""),
        transcript_text=transcript_data.get("full_text", ""),
        output_dir=out_dir
    )

    # Step 6: Assemble Core Intelligence Deliverables
    transcript_md = write_transcript_markdown(meta, transcript_data, out_dir)
    visual_report_md = write_visual_report_markdown(meta, frames, out_dir)
    strategies_sop_md = write_strategies_sop_markdown(meta, transcript_data.get("full_text", ""), out_dir)

    inventory = {
        "Transcript (Markdown)": transcript_md,
        "Visual Timeline Report": visual_report_md,
        "Operational SOP & Playbook": strategies_sop_md,
        "Mind Map (Mermaid View)": mindmaps["markdown_file"],
        "Obsidian Interactive Canvas": mindmaps["canvas_file"]
    }
    if comments_file and os.path.exists(comments_file):
        inventory["Community Comments & Insights"] = comments_file

    info_json = write_video_info_json(meta, out_dir)
    inventory["Structured Metadata (JSON)"] = info_json

    index_md = write_master_index_markdown(meta, inventory, out_dir)
    inventory["Knowledge Hub Index"] = index_md

    if not quiet:
        print("\n" + "=" * 65)
        print("  🎉 Pipeline Completed Successfully!")
        print(f"  Hub Index: {index_md}")
        print("=" * 65 + "\n")

    return {
        "status": "success",
        "title": title,
        "author": author,
        "output_dir": out_dir,
        "index_file": index_md,
        "inventory": inventory
    }


def process_playlist(
    url: str,
    output_dir: Optional[str] = None,
    extract_frames: bool = True,
    extract_comments: bool = True,
    force_whisper: bool = False,
    groq_api_key: Optional[str] = None,
    preferred_lang: str = "en,pt",
    quiet: bool = False
) -> Dict:
    """
    Batch processes an entire playlist.
    Creates a dedicated parent folder with subfolders for each media item and a master summary.
    """
    ensure_utf8_io()
    if not quiet:
        print(f"\n[>] Fetching playlist entries: {url}")

    ydl_opts = {
        "quiet": True,
        "extract_flat": "in_playlist",
        "skip_download": True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        playlist_info = ydl.extract_info(url, download=False)

    entries = playlist_info.get("entries") or []
    playlist_title = playlist_info.get("title") or "Playlist"
    total_videos = len(entries)

    parent_folder_name = f"Playlist - {playlist_title}"
    parent_dir = resolve_output_dir(output_dir, parent_folder_name)
    os.makedirs(parent_dir, exist_ok=True)

    if not quiet:
        print(f"[*] Playlist: {playlist_title} ({total_videos} videos)")
        print(f"[*] Destination: {parent_dir}\n")

    results = []
    summary_lines = [
        f"# Playlist Hub: {playlist_title}\n",
        f"- **Source URL:** {url}",
        f"- **Total Items:** {total_videos}",
        "\n---\n",
        "## 📑 Processed Videos & Playbooks\n",
        "| # | Video Title | Knowledge Hub | Transcript | Mind Map |",
        "| :-: | :--- | :--- | :--- | :--- |"
    ]

    for idx, entry in enumerate(entries, start=1):
        video_url = entry.get("url") or f"https://www.youtube.com/watch?v={entry.get('id')}"
        video_title = entry.get("title") or f"Video {idx}"
        clean_sub_name = f"{idx:02d} - {sanitize_filename(video_title)}"
        sub_output = os.path.join(parent_dir, clean_sub_name)

        if not quiet:
            print(f"\n[{idx}/{total_videos}] Processing: {video_title}")

        try:
            res = process_single_video(
                url=video_url,
                output_dir=sub_output,
                extract_frames=extract_frames,
                extract_comments=extract_comments,
                force_whisper=force_whisper,
                groq_api_key=groq_api_key,
                preferred_lang=preferred_lang,
                quiet=quiet
            )
            results.append(res)

            idx_uri = to_file_uri(res["index_file"])
            trans_uri = to_file_uri(res["inventory"]["Transcript (Markdown)"])
            mm_uri = to_file_uri(res["inventory"]["Mind Map (Mermaid View)"])

            summary_lines.append(
                f"| {idx} | **{video_title}** | [INDEX]({idx_uri}) | [Transcript]({trans_uri}) | [Mind Map]({mm_uri}) |"
            )

        except Exception as e:
            if not quiet:
                print(f"[-] Error processing {video_title}: {e}")
            summary_lines.append(f"| {idx} | **{video_title}** | *Error: {e}* | - | - |")

    # Write PLAYLIST_SUMMARY.md
    summary_path = os.path.join(parent_dir, "PLAYLIST_SUMMARY.md")
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("\n".join(summary_lines) + "\n")

    if not quiet:
        print("\n" + "=" * 65)
        print("  🎉 Entire Playlist Processed Successfully!")
        print(f"  Playlist Hub: {summary_path}")
        print("=" * 65 + "\n")

    return {
        "status": "success",
        "playlist_title": playlist_title,
        "total_items": total_videos,
        "parent_dir": parent_dir,
        "summary_file": summary_path,
        "results": results
    }
