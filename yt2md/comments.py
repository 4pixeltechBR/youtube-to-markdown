"""
yt2md.comments - Public comments extraction and sentiment/insight structuring.
Leverages yt-dlp native comment parsers without requiring YouTube Data API keys.
"""

import json
import os
from typing import Dict, List, Optional


def extract_comments_data(
    info_dict: dict,
    max_comments: int = 50,
    output_dir: Optional[str] = None
) -> Dict:
    """
    Extracts and parses comments from yt-dlp info dictionary.
    Categorizes into pinned comments and top upvoted community takeaways.
    """
    raw_comments = info_dict.get("comments") or []
    
    parsed_comments: List[Dict] = []
    pinned_comment: Optional[Dict] = None

    for c in raw_comments[:max_comments * 2]:
        text = c.get("text", "").strip()
        if not text:
            continue

        like_count = c.get("like_count") or 0
        author = c.get("author") or "Anonymous"
        is_favorited = bool(c.get("is_favorited", False))
        is_pinned = bool(c.get("is_pinned", False))
        timestamp = c.get("timestamp") or 0

        comment_obj = {
            "author": author,
            "text": text,
            "likes": like_count,
            "is_pinned": is_pinned,
            "is_favorited": is_favorited,
            "timestamp": timestamp
        }

        if is_pinned and not pinned_comment:
            pinned_comment = comment_obj
        else:
            parsed_comments.append(comment_obj)

    # Sort regular comments by likes descending
    parsed_comments.sort(key=lambda x: x["likes"], reverse=True)
    top_comments = parsed_comments[:max_comments]

    result = {
        "total_extracted": len(top_comments) + (1 if pinned_comment else 0),
        "pinned_comment": pinned_comment,
        "top_comments": top_comments
    }

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        json_path = os.path.join(output_dir, "comments.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

    return result


def format_comments_markdown(comments_data: Dict) -> str:
    """
    Renders comments into clean GitHub-flavored markdown.
    """
    lines = ["# Community Insights & Public Feedback\n"]

    pinned = comments_data.get("pinned_comment")
    if pinned:
        lines.append("## 📌 Pinned Creator Note / Resources\n")
        lines.append(f"> **@{pinned['author']}** ({pinned['likes']} likes):")
        for line in pinned["text"].splitlines():
            lines.append(f"> {line}")
        lines.append("\n---\n")

    top_comments = comments_data.get("top_comments", [])
    if top_comments:
        lines.append(f"## 💬 Top Community Discussions ({len(top_comments)} Most Relevant)\n")
        for idx, c in enumerate(top_comments, start=1):
            lines.append(f"### {idx}. @{c['author']} · 👍 {c['likes']}")
            lines.append(f"{c['text']}\n")
    else:
        lines.append("*No public comments available or comments are disabled on this media.*\n")

    return "\n".join(lines)
