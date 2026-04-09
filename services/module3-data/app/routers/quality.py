"""Data quality metrics for the scraped corpus."""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class QualityResponse(BaseModel):
    total_papers: int
    completeness_score: float
    consistency_score: float
    duplicate_rate: float
    sources: dict[str, int]


@router.get("/quality", response_model=QualityResponse)
async def data_quality() -> QualityResponse:
    """Compute completeness + consistency metrics over research_papers.

    TODO (Phase 4): Query Supabase, calculate % of papers with abstract/DOI/year,
    detect near-duplicates via embedding similarity, group counts by source.
    """
    return QualityResponse(
        total_papers=0,
        completeness_score=0.0,
        consistency_score=0.0,
        duplicate_rate=0.0,
        sources={},
    )
