"""
youtube-to-markdown (yt2md)
Universal multimodal reverse-engineering engine for AI agents & developers.
"""

from .cli import __version__, main
from .extractor import detect_playlist_intent, process_playlist, process_single_video
from .search import is_url, process_search_query, search_youtube
from .subtitles import extract_native_subtitles
from .transcriber import compress_audio, transcribe_with_groq
from .visual import extract_visual_timeline
from .comments import extract_comments_data
from .mindmap import build_mindmap_assets

__all__ = [
    "__version__",
    "main",
    "process_single_video",
    "process_playlist",
    "detect_playlist_intent",
    "search_youtube",
    "process_search_query",
    "is_url",
    "extract_native_subtitles",
    "transcribe_with_groq",
    "compress_audio",
    "extract_visual_timeline",
    "extract_comments_data",
    "build_mindmap_assets",
]
