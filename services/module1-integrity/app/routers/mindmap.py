"""Mind map builder — powered by Gemini concept extraction with a local fallback.

Output node `type` is one of: `central`, `primary`, `secondary`, `detail`.
The frontend uses these to colour the graph, so they MUST be assigned even
when Gemini is unavailable.
"""

from __future__ import annotations

import logging
import os
import sys

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()
logger = logging.getLogger(__name__)

_services_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, _services_root)


class GenerateMindMapRequest(BaseModel):
    text: str = Field(..., min_length=50)
    max_nodes: int = 30


class MindMapNode(BaseModel):
    id: str
    label: str
    type: str = "detail"   # central | primary | secondary | detail
    weight: float = 1.0


class MindMapEdge(BaseModel):
    source: str
    target: str
    weight: float = 1.0
    label: str = ""


class MindMap(BaseModel):
    nodes: list[MindMapNode]
    edges: list[MindMapEdge]


def _assign_tiers(nodes: list[MindMapNode]) -> None:
    """Bucket non-central nodes into primary / secondary / detail tiers based
    on their weight rank.

    Top 25% (excluding central) → primary
    Next 35%                    → secondary
    Remaining                   → detail
    Mutates `nodes` in-place.
    """
    non_central = [n for n in nodes if n.type != "central"]
    if not non_central:
        return
    # Sort by weight descending
    sorted_nodes = sorted(non_central, key=lambda n: n.weight, reverse=True)
    n = len(sorted_nodes)
    primary_cut = max(1, int(n * 0.25))
    secondary_cut = primary_cut + max(1, int(n * 0.35))
    for i, node in enumerate(sorted_nodes):
        if i < primary_cut:
            node.type = "primary"
        elif i < secondary_cut:
            node.type = "secondary"
        else:
            node.type = "detail"


@router.post("/generate", response_model=MindMap)
async def generate_mindmap(req: GenerateMindMapRequest) -> MindMap:
    """Extract key concepts and build a mind map. Tries Gemini first, falls
    back to a local term-frequency extractor when Gemini is unavailable."""
    max_nodes = min(req.max_nodes, 25)

    # ── 1. Gemini path ──────────────────────────────────────────────────
    try:
        from shared.gemini_client import generate_json

        text_snippet = req.text[:4000]
        prompt = f"""Analyze this academic text and extract key concepts for a mind map.

Text: {text_snippet}

Identify the central topic and {max_nodes - 1} related concepts. Group them into a hierarchical structure.

Return JSON:
{{
  "central": "main topic or central concept",
  "concepts": [
    {{"label": "concept name", "weight": 0.9, "related_to_central": true}},
    {{"label": "sub-concept", "weight": 0.7, "related_to_central": false, "parent": "concept name"}}
  ]
}}

weight: 0.1-1.0 (importance/relevance score)
Include at most {max_nodes - 1} concepts total."""

        data = generate_json(prompt)
        central = data.get("central", "Main Topic")
        concepts = data.get("concepts", [])

        nodes: list[MindMapNode] = [
            MindMapNode(id="node_0", label=central, type="central", weight=1.0),
        ]
        edges: list[MindMapEdge] = []
        label_to_id: dict[str, str] = {"central": "node_0", central: "node_0"}

        for i, c in enumerate(concepts[:max_nodes - 1], start=1):
            node_id = f"node_{i}"
            label = c.get("label", f"Concept {i}")
            weight = float(c.get("weight", 0.5))
            nodes.append(MindMapNode(id=node_id, label=label, type="detail", weight=round(weight, 3)))
            label_to_id[label] = node_id

            parent_label = c.get("parent")
            if parent_label and parent_label in label_to_id:
                edges.append(MindMapEdge(source=label_to_id[parent_label], target=node_id, weight=weight))
            else:
                edges.append(MindMapEdge(source="node_0", target=node_id, weight=weight))

        _assign_tiers(nodes)
        return MindMap(nodes=nodes, edges=edges)

    except Exception as e:
        logger.warning("Gemini mindmap failed (%s) — using local fallback", e)
        return _fallback_mindmap(req.text, max_nodes)


def _fallback_mindmap(text: str, max_nodes: int) -> MindMap:
    """Term-frequency fallback. The most frequent term becomes the central
    node, and tiers are assigned by weight."""
    import re
    from collections import Counter

    words = re.findall(r"\b[a-zA-Z]{4,}\b", text.lower())
    stop = {
        "this", "that", "with", "from", "have", "been", "were", "also",
        "they", "their", "which", "about", "using", "based", "paper", "method",
        "study", "research", "results", "approach", "system", "model", "data",
        "analysis", "such", "these", "those", "into", "more", "many", "some",
        "between", "among", "while", "than", "then", "there", "here", "show",
        "shown", "used", "uses", "used", "important", "different", "various",
    }
    words = [w for w in words if w not in stop]
    if not words:
        return MindMap(nodes=[], edges=[])

    freq = Counter(words).most_common(max_nodes)
    top_count = freq[0][1]

    nodes: list[MindMapNode] = []
    for i, (w, c) in enumerate(freq):
        weight = round(c / top_count, 3) if top_count else 0.0
        node_type = "central" if i == 0 else "detail"  # tiers refined below
        nodes.append(MindMapNode(id=f"node_{i}", label=w, type=node_type, weight=weight))

    edges = [MindMapEdge(source="node_0", target=f"node_{i}", weight=nodes[i].weight)
             for i in range(1, len(nodes))]

    _assign_tiers(nodes)
    return MindMap(nodes=nodes, edges=edges)
