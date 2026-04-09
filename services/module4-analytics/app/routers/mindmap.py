"""Concept mind map generator — GNN + KeyBERT."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()


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

    TODO (Phase 3/4): Extract concepts with KeyBERT, build co-occurrence graph,
    train/run 2-layer GCN on SBERT node features, output nodes+edges for D3.
    """
    return ConceptMap(nodes=[], edges=[])
