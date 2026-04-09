"""Gap analysis — SBERT + BERTopic to surface under-explored research areas."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()


class AnalyzeGapsRequest(BaseModel):
    topic: str = Field(..., min_length=1)
    corpus_size: int = 100


class ResearchGap(BaseModel):
    topic: str
    description: str
    gap_score: float
    recency_score: float
    novelty_score: float
    supporting_paper_ids: list[str] = []


class AnalyzeGapsResponse(BaseModel):
    gaps: list[ResearchGap]
    total_papers_analyzed: int


@router.post("/analyze", response_model=AnalyzeGapsResponse)
async def analyze_gaps(req: AnalyzeGapsRequest) -> AnalyzeGapsResponse:
    """Identify research gaps for a topic using semantic clustering.

    TODO (Phase 4): Query pgvector for top-K similar papers, cluster with BERTopic,
    score each cluster by recency + novelty, return under-represented clusters.
    """
    return AnalyzeGapsResponse(gaps=[], total_papers_analyzed=0)
