"""Concept mind map generator — GNN + KeyBERT."""

from __future__ import annotations

import logging

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ..models.mindmap_gnn import MindMapGNNModel

router = APIRouter()
logger = logging.getLogger(__name__)

_gnn_model: MindMapGNNModel | None = None


def _get_gnn() -> MindMapGNNModel:
    global _gnn_model
    if _gnn_model is None:
        _gnn_model = MindMapGNNModel()
    return _gnn_model


class MindMapRequest(BaseModel):
    department: str | None = None
    topic: str | None = None
    max_nodes: int = 50


class ConceptNode(BaseModel):
    id: str
    concept: str
    importance: float
    domain_cluster: str


class ConceptEdge(BaseModel):
    source: str
    target: str
    relationship_strength: float


class ConceptMap(BaseModel):
    nodes: list[ConceptNode]
    edges: list[ConceptEdge]


@router.post("/mindmap", response_model=ConceptMap)
async def generate_mindmap(req: MindMapRequest) -> ConceptMap:
    """Build a domain concept map via GCN + KeyBERT.

    1. If topic provided, use KeyBERT to extract seed concepts
    2. Feed seeds to GNN for concept graph expansion
    3. Return nodes + edges for D3 visualization
    """
    seed_concepts: list[str] = []

    if req.topic:
        # Extract key concepts via KeyBERT
        try:
            from keybert import KeyBERT
            kw_model = KeyBERT()
            keywords = kw_model.extract_keywords(
                req.topic,
                keyphrase_ngram_range=(1, 2),
                stop_words="english",
                top_n=5,
                use_mmr=True,
                diversity=0.5,
            )
            seed_concepts = [kw for kw, _ in keywords]
        except ImportError:
            seed_concepts = req.topic.split()[:5]
        except Exception as e:
            logger.warning("KeyBERT extraction failed: %s", e)
            seed_concepts = req.topic.split()[:5]

    if not seed_concepts and req.department:
        seed_concepts = [req.department]

    if not seed_concepts:
        seed_concepts = ["research"]

    # Use GNN model for graph expansion
    gnn = _get_gnn()
    try:
        mindmap_data = gnn.generate_mindmap(seed_concepts, max_nodes=req.max_nodes)
    except Exception as e:
        logger.warning("GNN mindmap generation failed: %s — using KeyBERT fallback", e)
        mindmap_data = {"nodes": [], "edges": []}

    # Convert to response schema
    nodes = []
    for n in mindmap_data.get("nodes", []):
        nodes.append(ConceptNode(
            id=str(n.get("id", "")),
            concept=n.get("label", ""),
            importance=float(n.get("weight", 0.5)),
            domain_cluster=n.get("domain_cluster", req.department or "general"),
        ))

    edges = []
    for e in mindmap_data.get("edges", []):
        edges.append(ConceptEdge(
            source=str(e.get("source", "")),
            target=str(e.get("target", "")),
            relationship_strength=float(e.get("weight", 0.5)),
        ))

    # If GNN returned nothing, build from KeyBERT seeds
    if not nodes and seed_concepts:
        for i, concept in enumerate(seed_concepts):
            nodes.append(ConceptNode(
                id=f"node_{i}",
                concept=concept,
                importance=1.0 - (i * 0.1),
                domain_cluster=req.department or "general",
            ))
        for i in range(1, len(nodes)):
            edges.append(ConceptEdge(
                source="node_0", target=f"node_{i}",
                relationship_strength=0.7,
            ))

    return ConceptMap(nodes=nodes, edges=edges)
