"""Mind map builder — KeyBERT key-phrase extraction + NetworkX graph."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()


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

    TODO (Phase 4): KeyBERT → extract top phrases → build NetworkX
    co-occurrence graph → return nodes + edges for D3 rendering.
    """
    return MindMap(nodes=[], edges=[])
