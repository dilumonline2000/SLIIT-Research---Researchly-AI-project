"""Mind map builder — powered by Gemini concept extraction."""

from __future__ import annotations

import logging
import sys
import os

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
    type: str = "concept"
    weight: float = 1.0


class MindMapEdge(BaseModel):
    source: str
    target: str
    weight: float = 1.0
    label: str = ""


class MindMap(BaseModel):
    nodes: list[MindMapNode]
    edges: list[MindMapEdge]


@router.post("/generate", response_model=MindMap)
async def generate_mindmap(req: GenerateMindMapRequest) -> MindMap:
    """Extract key concepts and build a mind map using Gemini."""
    from shared.gemini_client import generate_json

    max_nodes = min(req.max_nodes, 25)
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

    try:
        data = generate_json(prompt)
        central = data.get("central", "Main Topic")
        concepts = data.get("concepts", [])

        nodes: list[MindMapNode] = [
            MindMapNode(id="node_0", label=central, type="central", weight=1.0)
        ]
        edges: list[MindMapEdge] = []
        label_to_id: dict[str, str] = {"central": "node_0", central: "node_0"}

        for i, c in enumerate(concepts[:max_nodes - 1], start=1):
            node_id = f"node_{i}"
            label = c.get("label", f"Concept {i}")
            weight = float(c.get("weight", 0.5))
            nodes.append(MindMapNode(id=node_id, label=label, type="concept", weight=round(weight, 3)))
            label_to_id[label] = node_id

            parent_label = c.get("parent")
            if parent_label and parent_label in label_to_id:
                edges.append(MindMapEdge(source=label_to_id[parent_label], target=node_id, weight=weight))
            else:
                edges.append(MindMapEdge(source="node_0", target=node_id, weight=weight))

        return MindMap(nodes=nodes, edges=edges)

    except Exception as e:
        logger.error("Gemini mindmap generation failed: %s", e)
        return _fallback_mindmap(req.text, max_nodes)


def _fallback_mindmap(text: str, max_nodes: int) -> MindMap:
    import re
    from collections import Counter

    words = re.findall(r"\b[a-zA-Z]{4,}\b", text.lower())
    stop = {"this", "that", "with", "from", "have", "been", "were", "also", "they", "their", "which", "about", "using", "based", "paper", "method"}
    words = [w for w in words if w not in stop]
    freq = Counter(words).most_common(max_nodes)

    if not freq:
        return MindMap(nodes=[], edges=[])

    nodes = [MindMapNode(id=f"node_{i}", label=w, weight=round(c / freq[0][1], 3)) for i, (w, c) in enumerate(freq)]
    edges = [MindMapEdge(source="node_0", target=f"node_{i}", weight=0.5) for i in range(1, len(nodes))]
    return MindMap(nodes=nodes, edges=edges)
