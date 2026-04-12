"""Supervisor effectiveness scoring endpoint."""

from __future__ import annotations

import logging

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger(__name__)


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

    1. Query supervisor_matches for completion stats
    2. Query feedback_entries for sentiment averages
    3. Aggregate into weighted effectiveness score
    """
    try:
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "shared"))
        from services.shared.supabase_client import get_supabase_admin
    except ImportError:
        try:
            from shared.supabase_client import get_supabase_admin
        except ImportError:
            logger.warning("Shared utils not available")
            return _empty_response(supervisor_id)

    sb = get_supabase_admin()

    # Fetch supervisor matches
    try:
        matches_result = sb.table("supervisor_matches") \
            .select("*") \
            .eq("supervisor_id", supervisor_id) \
            .execute()
        matches = matches_result.data or []
    except Exception as e:
        logger.warning("Failed to fetch supervisor matches: %s", e)
        matches = []

    # Completion rate
    total_students = len(matches)
    completed = sum(1 for m in matches if m.get("status") == "completed")
    completion_rate = completed / max(total_students, 1)

    # Fetch feedback for this supervisor's students
    student_ids = [m.get("student_id") for m in matches if m.get("student_id")]
    feedback_sentiments: list[float] = []

    if student_ids:
        try:
            feedback_result = sb.table("feedback_entries") \
                .select("sentiment_score") \
                .in_("student_id", student_ids) \
                .execute()
            for fb in (feedback_result.data or []):
                score = fb.get("sentiment_score")
                if score is not None:
                    feedback_sentiments.append(float(score))
        except Exception as e:
            logger.warning("Failed to fetch feedback: %s", e)

    avg_sentiment = sum(feedback_sentiments) / max(len(feedback_sentiments), 1)

    # Student satisfaction — proxy from positive sentiment ratio
    positive_count = sum(1 for s in feedback_sentiments if s > 0.3)
    satisfaction = positive_count / max(len(feedback_sentiments), 1) if feedback_sentiments else 0.5

    # Weighted overall score
    overall = (
        completion_rate * 0.35 +
        max(0, min(1, (avg_sentiment + 1) / 2)) * 0.35 +  # normalize -1..1 to 0..1
        satisfaction * 0.30
    )

    return EffectivenessResponse(
        supervisor_id=supervisor_id,
        overall_score=round(overall, 3),
        completion_rate=round(completion_rate, 3),
        avg_feedback_sentiment=round(avg_sentiment, 3),
        student_satisfaction=round(satisfaction, 3),
        breakdown={
            "total_students": total_students,
            "completed": completed,
            "feedback_entries": len(feedback_sentiments),
            "weights": {"completion": 0.35, "sentiment": 0.35, "satisfaction": 0.30},
        },
    )


def _empty_response(supervisor_id: str) -> EffectivenessResponse:
    return EffectivenessResponse(
        supervisor_id=supervisor_id,
        overall_score=0.0, completion_rate=0.0,
        avg_feedback_sentiment=0.0, student_satisfaction=0.0,
        breakdown={},
    )
