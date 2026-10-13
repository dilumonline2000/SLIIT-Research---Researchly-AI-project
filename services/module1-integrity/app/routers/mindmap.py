"""Mind map builder — powered by Gemini concept extraction with a local fallback.

Two modes:

* ``concept``  – extract the key concepts from the text and show how they relate
  (the original behaviour).
* ``planner``  – read the *idea* behind an abstract and lay out how a student
  should plan and scope their research: problem, objectives, research
  questions, what to focus on, methodology steps, what to read, expected
  contribution, risks and next steps.

Output node ``type`` is one of: ``central``, ``primary``, ``secondary``,
``detail``. The frontend uses these to colour the graph, so they MUST be
assigned even when Gemini is unavailable.
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
    mode: str = "concept"   # concept | planner


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


class MindMapBranch(BaseModel):
    branch: str
    items: list[str] = []


class MindMap(BaseModel):
    nodes: list[MindMapNode]
    edges: list[MindMapEdge]
    mode: str = "concept"
    summary: str = ""                       # planner: one-line restatement of the idea
    outline: list[MindMapBranch] = []       # planner: branch → action items


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
    """Extract key concepts / build a research plan and return a mind map.
    Tries Gemini first, falls back to a local extractor when Gemini is
    unavailable."""
    max_nodes = min(req.max_nodes, 25)

    if req.mode == "planner":
        try:
            return _planner_mindmap(req.text, max_nodes)
        except Exception as e:
            logger.warning("Gemini planner mindmap failed (%s) — using local fallback", e)
            return _planner_fallback(req.text)

    # ── Concept mode ────────────────────────────────────────────────────
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

        # Bounded so the request stays inside the gateway/browser timeout — on a
        # slow or overloaded Gemini we fall back to the local extractor instead.
        data = generate_json(prompt, timeout=25)
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
        return MindMap(nodes=nodes, edges=edges, mode="concept")

    except Exception as e:
        logger.warning("Gemini mindmap failed (%s) — using local fallback", e)
        return _fallback_mindmap(req.text, max_nodes)


# ── Planner mode ────────────────────────────────────────────────────────

# The branches we want the plan organised around. Gemini is told to keep these
# names and fill each one with concrete, text-specific action items.
# Cap the item nodes drawn per branch so the radial map stays legible. The
# full item list is always returned in `outline` for the panel below the map.
_MAX_ITEMS_ON_GRAPH = 3

_PLANNER_BRANCHES = [
    "Research Problem & Gap",
    "Aim & Objectives",
    "Research Questions",
    "Scope & Focus",
    "Methodology Steps",
    "Literature to Review",
    "Data & Tools Needed",
    "Expected Contribution",
    "Risks & Challenges",
    "Next Steps",
]


def _planner_mindmap(text: str, max_nodes: int) -> MindMap:
    """Turn an abstract into a research-planning mind map via Gemini."""
    from shared.gemini_client import generate_json

    text_snippet = text[:4000]
    branch_list = "\n".join(f"  - {b}" for b in _PLANNER_BRANCHES)
    prompt = f"""You are a research supervisor helping an undergraduate student turn the
idea in this abstract into a plan they can actually execute.

Abstract / research description:
{text_snippet}

Do NOT just list keywords. Read the underlying idea and explain how the student
should plan and scope the work, and what to focus on first.

Organise the plan under these branches (keep the exact branch names):
{branch_list}

For every branch give 2-4 short, concrete, actionable items grounded in THIS
abstract (not generic advice). Each item <= 12 words.

Return JSON:
{{
  "topic": "a 3-6 word name for the research",
  "summary": "one sentence: what the student is trying to achieve and why",
  "branches": [
    {{"branch": "Research Problem & Gap", "items": ["...", "..."]}},
    {{"branch": "Aim & Objectives", "items": ["...", "..."]}}
  ]
}}
"""

    # Bounded so the request stays inside the gateway/browser timeout — on a
    # slow or overloaded Gemini we fall back to the template plan instead.
    data = generate_json(prompt, timeout=25)
    topic = (data.get("topic") or "Research Plan").strip()
    summary = (data.get("summary") or "").strip()
    raw_branches = data.get("branches") or []

    nodes: list[MindMapNode] = [
        MindMapNode(id="node_0", label=topic, type="central", weight=1.0),
    ]
    edges: list[MindMapEdge] = []
    outline: list[MindMapBranch] = []

    node_i = 1
    total_branches = max(1, len(raw_branches))
    for b_idx, b in enumerate(raw_branches):
        branch_label = str(b.get("branch") or f"Branch {b_idx + 1}").strip()
        items = [str(x).strip() for x in (b.get("items") or []) if str(x).strip()]
        if not branch_label:
            continue

        # Branch weight fades from 0.95 → 0.55 by position so the layout keeps
        # the earlier (more foundational) branches visually prominent.
        branch_weight = round(0.95 - 0.4 * (b_idx / total_branches), 3)
        branch_id = f"node_{node_i}"
        node_i += 1
        nodes.append(MindMapNode(id=branch_id, label=branch_label, type="primary", weight=branch_weight))
        edges.append(MindMapEdge(source="node_0", target=branch_id, weight=branch_weight, label="plan"))

        outline.append(MindMapBranch(branch=branch_label, items=items))

        # Only the first few items go on the graph (kept readable); the full
        # list still shows in the outline panel under the map.
        for item in items[:_MAX_ITEMS_ON_GRAPH]:
            if node_i >= max_nodes:
                break
            item_id = f"node_{node_i}"
            node_i += 1
            nodes.append(MindMapNode(id=item_id, label=item, type="secondary", weight=0.4))
            edges.append(MindMapEdge(source=branch_id, target=item_id, weight=0.4))
        if node_i >= max_nodes:
            break

    if len(nodes) <= 1:
        raise RuntimeError("planner returned no branches")

    return MindMap(nodes=nodes, edges=edges, mode="planner", summary=summary, outline=outline)


def _planner_fallback(text: str) -> MindMap:
    """Template research plan used when Gemini is unavailable. Generic guidance,
    seeded with a few salient terms from the text so it is not entirely blind."""
    import re
    from collections import Counter

    words = re.findall(r"\b[a-zA-Z]{5,}\b", text.lower())
    stop = {
        "which", "these", "those", "there", "their", "about", "using", "based",
        "study", "research", "results", "approach", "system", "model", "using",
        "between", "among", "while", "there", "paper", "method", "should",
        "could", "would", "propose", "proposed", "present", "presents",
    }
    terms = [w for w in words if w not in stop]
    top_terms = [w for w, _ in Counter(terms).most_common(4)] or ["your topic"]
    focus = ", ".join(top_terms[:3])

    plan: list[tuple[str, list[str]]] = [
        ("Research Problem & Gap", [
            f"State the specific problem around {top_terms[0]}",
            "Find what prior work has NOT solved",
            "Justify why the gap matters",
        ]),
        ("Aim & Objectives", [
            "Write one overall aim",
            "Break it into 3-4 measurable objectives",
            "Make each objective verifiable",
        ]),
        ("Research Questions", [
            "Turn each objective into a question",
            "Keep questions answerable within your timeframe",
        ]),
        ("Scope & Focus", [
            f"Focus first on: {focus}",
            "List what is explicitly out of scope",
            "Fix dataset / domain boundaries early",
        ]),
        ("Methodology Steps", [
            "Data collection and preparation",
            "Build baseline, then proposed method",
            "Define evaluation metrics up front",
            "Plan an ablation / comparison",
        ]),
        ("Literature to Review", [
            f"Key themes: {focus}",
            "Find 3-5 seminal papers",
            "Track recent (last 2 years) work",
        ]),
        ("Data & Tools Needed", [
            "List required datasets and access",
            "Pick frameworks and compute early",
            "Note ethics / consent if human data",
        ]),
        ("Expected Contribution", [
            "State the novelty in one sentence",
            "Decide how you will demonstrate it",
        ]),
        ("Risks & Challenges", [
            "Data scarcity or quality",
            "Generalisation beyond your sample",
            "Reproducibility and time budget",
        ]),
        ("Next Steps", [
            "Draft the problem statement this week",
            "Assemble the reading list",
            "Prototype the smallest end-to-end pipeline",
        ]),
    ]

    nodes: list[MindMapNode] = [
        MindMapNode(id="node_0", label="Research Plan", type="central", weight=1.0),
    ]
    edges: list[MindMapEdge] = []
    outline: list[MindMapBranch] = []

    node_i = 1
    n_branches = len(plan)
    for b_idx, (branch_label, items) in enumerate(plan):
        branch_weight = round(0.95 - 0.4 * (b_idx / n_branches), 3)
        branch_id = f"node_{node_i}"
        node_i += 1
        nodes.append(MindMapNode(id=branch_id, label=branch_label, type="primary", weight=branch_weight))
        edges.append(MindMapEdge(source="node_0", target=branch_id, weight=branch_weight, label="plan"))
        outline.append(MindMapBranch(branch=branch_label, items=items))
        for item in items[:_MAX_ITEMS_ON_GRAPH]:
            item_id = f"node_{node_i}"
            node_i += 1
            nodes.append(MindMapNode(id=item_id, label=item, type="secondary", weight=0.4))
            edges.append(MindMapEdge(source=branch_id, target=item_id, weight=0.4))

    return MindMap(
        nodes=nodes,
        edges=edges,
        mode="planner",
        summary="Template plan (AI planner unavailable) — edit each branch to fit your abstract.",
        outline=outline,
    )


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
    return MindMap(nodes=nodes, edges=edges, mode="concept")
