"""Mind map builder — KeyBERT key-phrase extraction + NetworkX graph."""

from __future__ import annotations

import logging
from collections import defaultdict

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()
logger = logging.getLogger(__name__)


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
    """Extract key phrases and build a concept graph.

    1. KeyBERT extracts top-N key phrases from the input text
    2. Build co-occurrence graph: phrases that appear in the same sentence are linked
    3. NetworkX computes centrality for node sizing
    4. Return nodes + edges for D3 rendering
    """
    try:
        from keybert import KeyBERT
    except ImportError:
        logger.warning("keybert not installed — using fallback extraction")
        return _fallback_mindmap(req.text, req.max_nodes)

    try:
        import networkx as nx
    except ImportError:
        logger.warning("networkx not installed")
        return _fallback_mindmap(req.text, req.max_nodes)

    # Step 1: Extract key phrases
    kw_model = KeyBERT()
    keywords = kw_model.extract_keywords(
        req.text,
        keyphrase_ngram_range=(1, 3),
        stop_words="english",
        top_n=min(req.max_nodes, 30),
        use_mmr=True,
        diversity=0.5,
    )

    if not keywords:
        return MindMap(nodes=[], edges=[])

    # Step 2: Build co-occurrence graph
    import re
    sentences = re.split(r"(?<=[.!?])\s+", req.text)
    phrase_list = [kw for kw, _ in keywords]

    G = nx.Graph()
    for phrase, score in keywords:
        G.add_node(phrase, weight=score)

    # Link phrases co-occurring in the same sentence
    for sent in sentences:
        sent_lower = sent.lower()
        present = [p for p in phrase_list if p.lower() in sent_lower]
        for i in range(len(present)):
            for j in range(i + 1, len(present)):
                if G.has_edge(present[i], present[j]):
                    G[present[i]][present[j]]["weight"] += 0.1
                else:
                    G.add_edge(present[i], present[j], weight=0.5)

    # Add edges from highest-score keyword to all others (central topic)
    central = phrase_list[0]
    for phrase in phrase_list[1:]:
        if not G.has_edge(central, phrase):
            G.add_edge(central, phrase, weight=0.3)

    # Step 3: Compute centrality for node sizing
    try:
        centrality = nx.degree_centrality(G)
    except Exception:
        centrality = {n: 1.0 for n in G.nodes()}

    # Build response
    nodes = []
    for i, (phrase, score) in enumerate(keywords):
        node_type = "central" if i == 0 else "concept"
        nodes.append(MindMapNode(
            id=f"node_{i}",
            label=phrase,
            type=node_type,
            weight=round(score * (1 + centrality.get(phrase, 0)), 3),
        ))

    phrase_to_id = {phrase: f"node_{i}" for i, (phrase, _) in enumerate(keywords)}
    edges = []
    for u, v, data in G.edges(data=True):
        if u in phrase_to_id and v in phrase_to_id:
            edges.append(MindMapEdge(
                source=phrase_to_id[u],
                target=phrase_to_id[v],
                weight=round(data.get("weight", 0.5), 3),
            ))

    return MindMap(nodes=nodes, edges=edges)


def _fallback_mindmap(text: str, max_nodes: int) -> MindMap:
    """Simple TF-based extraction when KeyBERT is unavailable."""
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
