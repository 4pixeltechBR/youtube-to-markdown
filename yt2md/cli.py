"""
yt2md.cli - Command-line interface and harness bridge.
"""

import argparse
import json
import os
import sys

from .extractor import (
    detect_playlist_intent,
    process_playlist,
    process_single_video,
)
from .utils import ensure_utf8_io

ensure_utf8_io()

__version__ = "1.0.0"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="yt2md",
        description="youtube-to-markdown: Turn YouTube, playlists & media into structured Markdown, Whisper transcripts, frame timelines & Obsidian/Mermaid mind maps."
    )
    parser.add_argument(
        "url",
        nargs="?",
        help="Target media URL (YouTube video, playlist, TikTok, Instagram Reel, X/Twitter, podcast)."
    )
    parser.add_argument(
        "-o", "--output",
        dest="output",
        default=None,
        help="Destination directory for generated files (defaults to interactive prompt or ./output/<title>)."
    )
    parser.add_argument(
        "--playlist",
        dest="force_playlist",
        action="store_true",
        help="Force batch processing of the entire playlist if detected."
    )
    parser.add_argument(
        "--single-video",
        dest="force_single",
        action="store_true",
        help="Force processing only the single video when given a playlist link."
    )
    parser.add_argument(
        "--no-frames",
        dest="extract_frames",
        action="store_false",
        default=True,
        help="Skip downloading 720p video and extracting 16 visual frames (faster, audio/text only)."
    )
    parser.add_argument(
        "--no-comments",
        dest="extract_comments",
        action="store_false",
        default=True,
        help="Skip extracting public comments & feedback."
    )
    parser.add_argument(
        "--force-whisper",
        dest="force_whisper",
        action="store_true",
        help="Bypass native captions (CC) and force Groq Whisper v3 Turbo neural transcription."
    )
    parser.add_argument(
        "--groq-key",
        dest="groq_key",
        default=None,
        help="Custom Groq API Key (or set GROQ_API_KEY environment variable)."
    )
    parser.add_argument(
        "--lang",
        dest="lang",
        default="en,pt",
        help="Comma-separated preferred languages for captions/Whisper (default: 'en,pt')."
    )
    parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="Output raw machine-readable JSON to stdout (recommended for AI agent harnesses)."
    )
    parser.add_argument(
        "-q", "--quiet",
        dest="quiet",
        action="store_true",
        help="Suppress banner and progress messages."
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"youtube-to-markdown v{__version__}"
    )
    return parser


def main():
    ensure_utf8_io()
    parser = build_parser()
    args = parser.parse_args()

    if not args.url:
        if sys.stdin.isatty():
            print("\n  🎬 youtube-to-markdown v" + __version__)
            try:
                args.url = input("  Enter media or playlist URL: ").strip()
            except (KeyboardInterrupt, EOFError):
                sys.exit(0)
        if not args.url:
            parser.print_help()
            sys.exit(1)

    quiet_mode = args.quiet or args.json_output

    try:
        intent = detect_playlist_intent(
            args.url,
            force_playlist=args.force_playlist,
            force_single=args.force_single
        )

        if intent == "playlist":
            result = process_playlist(
                url=args.url,
                output_dir=args.output,
                extract_frames=args.extract_frames,
                extract_comments=args.extract_comments,
                force_whisper=args.force_whisper,
                groq_api_key=args.groq_key,
                preferred_lang=args.lang,
                quiet=quiet_mode
            )
        else:
            result = process_single_video(
                url=args.url,
                output_dir=args.output,
                extract_frames=args.extract_frames,
                extract_comments=args.extract_comments,
                force_whisper=args.force_whisper,
                groq_api_key=args.groq_key,
                preferred_lang=args.lang,
                quiet=quiet_mode
            )

        if args.json_output:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0)

    except KeyboardInterrupt:
        print("\n[!] Execution interrupted by user.")
        sys.exit(130)
    except Exception as e:
        if args.json_output:
            print(json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False))
        else:
            print(f"\n[❌ ERROR] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
