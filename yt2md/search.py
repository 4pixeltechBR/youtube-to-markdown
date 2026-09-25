"""
yt2md.search - YouTube keyword search, interactive selection, and batch search processing.
Enables discovering and reverse-engineering videos directly from search queries without pre-copied URLs.
"""

import os
import sys
from typing import Dict, List, Optional
import yt_dlp

from .extractor import is_interactive, process_single_video, resolve_output_dir
from .utils import ensure_utf8_io, format_timestamp, sanitize_filename, to_file_uri


def is_url(text: str) -> bool:
    """Checks whether the given string is a web URL."""
    if not text:
        return False
    text = text.strip()
    return (
        text.startswith("http://")
        or text.startswith("https://")
        or text.startswith("www.")
        or text.startswith("youtu.be/")
    )


def search_youtube(query: str, limit: int = 5) -> List[Dict]:
    """
    Searches YouTube natively using yt-dlp ytsearch syntax without requiring Google API keys.
    """
    ensure_utf8_io()
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": "in_playlist",
        "skip_download": True,
    }

    search_target = f"ytsearch{limit}:{query}"
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        res = ydl.extract_info(search_target, download=False)

    entries = res.get("entries") or []
    results = []

    for entry in entries:
        video_id = entry.get("id")
        raw_url = entry.get("url")
        if raw_url and (raw_url.startswith("http://") or raw_url.startswith("https://")):
            url = raw_url
        elif video_id:
            url = f"https://www.youtube.com/watch?v={video_id}"
        else:
            continue

        results.append({
            "id": video_id,
            "title": entry.get("title") or "Untitled Video",
            "uploader": entry.get("uploader") or entry.get("channel") or "Unknown Channel",
            "duration": float(entry.get("duration") or 0.0),
            "view_count": entry.get("view_count") or 0,
            "url": url
        })

    return results


def process_search_query(
    query: str,
    limit: int = 5,
    process_all: bool = False,
    selected_index: Optional[int] = None,
    output_dir: Optional[str] = None,
    extract_frames: bool = True,
    extract_comments: bool = True,
    force_whisper: bool = False,
    groq_api_key: Optional[str] = None,
    preferred_lang: str = "en,pt",
    quiet: bool = False
) -> Dict:
    """
    Orchestrates searching YouTube, displaying interactive selection, and processing chosen videos.
    """
    ensure_utf8_io()
    if not quiet:
        print(f"\n[🔍] Searching YouTube for: \"{query}\" (Top {limit} results)...")

    results = search_youtube(query, limit=limit)
    if not results:
        raise RuntimeError(f"No YouTube videos found matching query: \"{query}\"")

    chosen_mode = None
    target_video = None

    # Handle explicit index or process_all flags
    if process_all:
        chosen_mode = "all"
    elif selected_index is not None and 1 <= selected_index <= len(results):
        chosen_mode = "single"
        target_video = results[selected_index - 1]

    # Interactive prompt if mode not decided
    if chosen_mode is None:
        if is_interactive():
            print("\n" + "=" * 70)
            print(f"  🔍 YouTube Search Results: \"{query}\"")
            print("=" * 70)
            for idx, item in enumerate(results, start=1):
                dur_str = format_timestamp(item["duration"])
                views_str = f"{item['view_count']:,}" if item["view_count"] else "N/A"
                print(f"  [{idx}] {item['title']}")
                print(f"      Channel: {item['uploader']}  |  Duration: {dur_str}  |  Views: {views_str}")
                print(f"      URL: {item['url']}\n")

            print("-" * 70)
            print("  Options:")
            print(f"  [1-{len(results)}] Process specific video (recommended)")
            print("  [A]     Process ALL in batch (creates comparative search hub)")
            print("  [Q]     Quit / Cancel")
            print("=" * 70)

            while True:
                try:
                    choice = input(f"  Select option [1-{len(results)} / A / Q, default: 1]: ").strip()
                except (KeyboardInterrupt, EOFError):
                    sys.exit(0)

                if not choice or choice == "1":
                    chosen_mode = "single"
                    target_video = results[0]
                    break
                elif choice.upper() == "A":
                    chosen_mode = "all"
                    break
                elif choice.upper() == "Q":
                    print("[!] Search cancelled.")
                    sys.exit(0)
                elif choice.isdigit() and 1 <= int(choice) <= len(results):
                    chosen_mode = "single"
                    target_video = results[int(choice) - 1]
                    break
                else:
                    print(f"  Invalid option. Please enter 1-{len(results)}, A, or Q.")
        else:
            # Headless / agent mode default: process top #1 result
            chosen_mode = "single"
            target_video = results[0]

    # 1. Process single video
    if chosen_mode == "single" and target_video:
        if not quiet:
            print(f"\n[>] Selected #{results.index(target_video)+1}: {target_video['title']}")
        return process_single_video(
            url=target_video["url"],
            output_dir=output_dir,
            extract_frames=extract_frames,
            extract_comments=extract_comments,
            force_whisper=force_whisper,
            groq_api_key=groq_api_key,
            preferred_lang=preferred_lang,
            quiet=quiet
        )

    # 2. Process all search results in batch
    parent_folder_name = f"Search - {sanitize_filename(query)}"
    parent_dir = resolve_output_dir(output_dir, parent_folder_name)
    os.makedirs(parent_dir, exist_ok=True)

    if not quiet:
        print(f"\n[*] Processing all {len(results)} search results into: {parent_dir}\n")

    batch_results = []
    summary_lines = [
        f"# Search Intelligence Hub: \"{query}\"\n",
        f"- **Search Query:** `{query}`",
        f"- **Total Ingested:** {len(results)} videos",
        "\n---\n",
        "## 📑 Processed Results & Playbooks\n",
        "| # | Video Title | Channel | Duration | Knowledge Hub | Transcript | Mind Map |",
        "| :-: | :--- | :--- | :-: | :--- | :--- | :--- |"
    ]

    for idx, item in enumerate(results, start=1):
        clean_sub_name = f"{idx:02d} - {sanitize_filename(item['title'])}"
        sub_output = os.path.join(parent_dir, clean_sub_name)

        if not quiet:
            print(f"\n[{idx}/{len(results)}] Ingesting: {item['title']} ({item['uploader']})")

        try:
            res = process_single_video(
                url=item["url"],
                output_dir=sub_output,
                extract_frames=extract_frames,
                extract_comments=extract_comments,
                force_whisper=force_whisper,
                groq_api_key=groq_api_key,
                preferred_lang=preferred_lang,
                quiet=quiet
            )
            batch_results.append(res)

            idx_uri = to_file_uri(res["index_file"])
            trans_uri = to_file_uri(res["inventory"]["Transcript (Markdown)"])
            mm_uri = to_file_uri(res["inventory"]["Mind Map (Mermaid View)"])
            dur_str = format_timestamp(item["duration"])

            summary_lines.append(
                f"| {idx} | **{item['title']}** | {item['uploader']} | `{dur_str}` | [INDEX]({idx_uri}) | [Transcript]({trans_uri}) | [Mind Map]({mm_uri}) |"
            )
        except Exception as e:
            if not quiet:
                print(f"[-] Error processing {item['title']}: {e}")
            summary_lines.append(f"| {idx} | **{item['title']}** | {item['uploader']} | - | *Error: {e}* | - | - |")

    summary_file = os.path.join(parent_dir, "SEARCH_SUMMARY.md")
    with open(summary_file, "w", encoding="utf-8") as f:
        f.write("\n".join(summary_lines) + "\n")

    if not quiet:
        print("\n" + "=" * 70)
        print("  🎉 Search Batch Completed Successfully!")
        print(f"  Summary Hub: {summary_file}")
        print("=" * 70 + "\n")

    return {
        "status": "success",
        "search_query": query,
        "total_results": len(results),
        "parent_dir": parent_dir,
        "summary_file": summary_file,
        "results": batch_results
    }
