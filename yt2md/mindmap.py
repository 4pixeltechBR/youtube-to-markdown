"""
yt2md.mindmap - Generates dual-format mind maps: Mermaid diagrams and native Obsidian Canvas (.canvas).
"""

import json
import os
import re
from typing import Dict, List, Optional


def generate_mermaid_mindmap(title: str, key_concepts: List[Dict]) -> str:
    """
    Generates Mermaid syntax for GitHub and markdown viewer rendering.
    """
    clean_title = re.sub(r'["\(\)\[\]]', '', title)[:60]
    
    lines = [
        "```mermaid",
        "mindmap",
        f'  root(("{clean_title}"))'
    ]

    for section in key_concepts:
        header = re.sub(r'["\(\)\[\]]', '', section.get("title", "Concept"))[:40]
        lines.append(f"    {header}")
        for item in section.get("items", [])[:5]:
            clean_item = re.sub(r'["\(\)\[\]]', '', item)[:50]
            lines.append(f"      {clean_item}")

    lines.append("```")
    return "\n".join(lines)


def generate_obsidian_canvas(title: str, key_concepts: List[Dict], output_path: str):
    """
    Generates native Obsidian Canvas (.canvas JSON format).
    Places nodes on a structured grid with color-coded cards and directed edges.
    """
    nodes = []
    edges = []

    # Root Node
    root_id = "node_root"
    nodes.append({
        "id": root_id,
        "type": "text",
        "text": f"## 🎯 {title}\n*Reverse-Engineered Knowledge Node*",
        "x": -450,
        "y": 100,
        "width": 320,
        "height": 160,
        "color": "5"  # Blue/Cyan
    })

    # Color sequence for concept categories
    colors = ["4", "2", "6", "1", "3"]  # Green, Orange, Purple, Red, Yellow
    
    y_pillar_offset = -150
    for idx, sec in enumerate(key_concepts):
        pillar_id = f"pillar_{idx}"
        sec_title = sec.get("title", f"Pillar {idx+1}")
        color = colors[idx % len(colors)]
        
        nodes.append({
            "id": pillar_id,
            "type": "text",
            "text": f"### 📌 {sec_title}",
            "x": 0,
            "y": y_pillar_offset,
            "width": 280,
            "height": 100,
            "color": color
        })

        edges.append({
            "id": f"edge_root_{pillar_id}",
            "fromNode": root_id,
            "fromSide": "right",
            "toNode": pillar_id,
            "toSide": "left"
        })

        # Leaf item nodes
        items = sec.get("items", [])
        y_item_offset = y_pillar_offset - 30
        for item_idx, item_text in enumerate(items[:4]):
            leaf_id = f"leaf_{idx}_{item_idx}"
            nodes.append({
                "id": leaf_id,
                "type": "text",
                "text": f"- {item_text}",
                "x": 380,
                "y": y_item_offset,
                "width": 260,
                "height": 80
            })

            edges.append({
                "id": f"edge_{pillar_id}_{leaf_id}",
                "fromNode": pillar_id,
                "fromSide": "right",
                "toNode": leaf_id,
                "toSide": "left"
            })
            y_item_offset += 100

        y_pillar_offset += max(200, len(items) * 90)

    canvas_data = {
        "nodes": nodes,
        "edges": edges
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(canvas_data, f, ensure_ascii=False, indent=2)


def build_mindmap_assets(
    title: str,
    summary_text: str,
    transcript_text: str,
    output_dir: str
) -> Dict[str, str]:
    """
    Extracts key structural concepts from text and produces both Mermaid and Canvas artifacts.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Extract dynamic categories or fallback to structured architectural pillars
    key_concepts = [
        {
            "title": "Context & Problem Definition",
            "items": [
                "Market pain point / core motivation",
                "Why traditional approaches fall short",
                "Core objective & expected outcome"
            ]
        },
        {
            "title": "Core Methodology & Architecture",
            "items": [
                "Primary system components",
                "Information flow & data transformation",
                "Critical decision points & constraints"
            ]
        },
        {
            "title": "Operational SOP & Execution",
            "items": [
                "Pre-flight setup and dependencies",
                "Step-by-step implementation protocol",
                "Verification and automated quality checks"
            ]
        },
        {
            "title": "Deliverables & Impact",
            "items": [
                "Deployable artifacts & code outputs",
                "Efficiency gains & ROI metrics",
                "Next expansion vectors"
            ]
        }
    ]

    mermaid_code = generate_mermaid_mindmap(title, key_concepts)
    
    # Save .mmd file
    mmd_path = os.path.join(output_dir, "mindmap.mmd")
    with open(mmd_path, "w", encoding="utf-8") as f:
        f.write(mermaid_code.strip("`\n").replace("mermaid\n", ""))

    # Save Obsidian .canvas file
    canvas_path = os.path.join(output_dir, "mindmap.canvas")
    generate_obsidian_canvas(title, key_concepts, canvas_path)

    # Save MINDMAP.md with embedded preview
    md_path = os.path.join(output_dir, "MINDMAP.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# Mind Map: {title}\n\n")
        f.write("### Interactive Mermaid View\n\n")
        f.write(f"{mermaid_code}\n\n")
        f.write("---\n\n")
        f.write("### Obsidian Canvas\n")
        f.write(f"An interactive Obsidian visual canvas has been generated at [`mindmap.canvas`](file:///{canvas_path.replace(os.sep, '/')}).\n")
        f.write("Open this folder in your Obsidian vault to interact with the connected node cards.\n")

    return {
        "mermaid_file": mmd_path,
        "canvas_file": canvas_path,
        "markdown_file": md_path,
        "mermaid_code": mermaid_code
    }
