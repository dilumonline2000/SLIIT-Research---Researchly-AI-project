"""Quality scoring endpoint — weighted multi-dimensional evaluation."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()


class QualityScoreRequest(BaseModel):
    proposal_id: str
    user_id: str


class QualityScoreResponse(BaseModel):
    proposal_id: str
    overall_score: float
    originality_score: float       # 30% weight
    citation_impact_score: float   # 25% weight
    methodology_score: float       # 25% weight
    clarity_score: float           # 20% weight
    breakdown: dict


@router.post("/quality-score", response_model=QualityScoreResponse)
async def quality_score(req: QualityScoreRequest) -> QualityScoreResponse:
    """Compute weighted multi-dimensional quality score.

    Weights per spec: originality 30% + citation_impact 25% + methodology 25% + clarity 20%.
    TODO (Phase 4): Combine plagiarism check (originality), citation graph impact,
    methodology detection, readability metrics.
    """
    return QualityScoreResponse(
        proposal_id=req.proposal_id,
        overall_score=0.0,
        originality_score=0.0,
        citation_impact_score=0.0,
        methodology_score=0.0,
        clarity_score=0.0,
        breakdown={},
    )
