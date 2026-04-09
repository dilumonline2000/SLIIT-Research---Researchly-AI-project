"""Supervisor effectiveness scoring endpoint."""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class EffectivenessResponse(BaseModel):
    supervisor_id: str
    overall_score: float
    completion_rate: float
    avg_feedback_sentiment: float
    student_satisfaction: float
    breakdown: dict


@router.get("/{supervisor_id}", response_model=EffectivenessResponse)
async def get_effectiveness(supervisor_id: str) -> EffectivenessResponse:
    """Compute multi-dimensional supervisor effectiveness score.

    TODO (Phase 4): Query feedback_entries + supervisor_matches, aggregate,
    produce weighted score and breakdown.
    """
    return EffectivenessResponse(
        supervisor_id=supervisor_id,
        overall_score=0.0,
        completion_rate=0.0,
        avg_feedback_sentiment=0.0,
        student_satisfaction=0.0,
        breakdown={},
    )
