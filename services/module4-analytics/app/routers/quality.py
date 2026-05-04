"""Quality scoring endpoint — uses trained XGBoost models on SLIIT papers."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..services import quality_predictor, topic_classifier

router = APIRouter()
logger = logging.getLogger(__name__)


WEIGHTS = {
    "originality": 0.30,
    "citation_impact": 0.25,
    "methodology": 0.25,
    "clarity": 0.20,
}


class QualityScoreRequest(BaseModel):
    proposal_id: str | None = None
    user_id: str | None = None
    title: str | None = None
    abstract: str | None = None


class QualityScoreResponse(BaseModel):
    proposal_id: str | None
    overall_score: float
    originality_score: float
    citation_impact_score: float
    methodology_score: float
    clarity_score: float
    topic: dict | None
    breakdown: dict
    recommendations: list[str]
    model_version: str


def _fetch_proposal_text(proposal_id: str) -> dict | None:
    """Fetch proposal from Supabase if available."""
    try:
        try:
            from services.shared.supabase_client import get_supabase_admin
        except ImportError:
            from shared.supabase_client import get_supabase_admin

        sb = get_supabase_admin()
        result = sb.table("research_proposals").select("*").eq("id", proposal_id).single().execute()
        return result.data
    except Exception as e:
        logger.warning("Failed to fetch proposal %s: %s", proposal_id, e)
        return None


def _store_score(proposal_id: str, user_id: str | None, scores: dict) -> None:
    """Persist score to Supabase."""
    try:
        try:
            from services.shared.supabase_client import get_supabase_admin
        except ImportError:
            from shared.supabase_client import get_supabase_admin

        sb = get_supabase_admin()
        sb.table("quality_scores").upsert({
            "proposal_id": proposal_id,
            "user_id": user_id,
            "overall_score": scores["overall_score"],
            "originality_score": scores["originality_score"],
            "citation_impact_score": scores["citation_impact_score"],
            "methodology_score": scores["methodology_score"],
            "clarity_score": scores["clarity_score"],
        }).execute()
    except Exception as e:
        logger.warning("Failed to store score: %s", e)


@router.post("/quality-score", response_model=QualityScoreResponse)
async def quality_score(req: QualityScoreRequest) -> QualityScoreResponse:
    """Compute quality score using trained XGBoost models.

    Accepts either:
    - proposal_id (will fetch from Supabase)
    - title + abstract (direct text analysis)
    """
    title = req.title or ""
    abstract = req.abstract or ""
    authors = None
    year = None

    # If proposal_id given, fetch from DB
    if req.proposal_id and not abstract:
        proposal = _fetch_proposal_text(req.proposal_id)
        if proposal:
            title = title or proposal.get("title", "")
            abstract = proposal.get("abstract", "") or proposal.get("methodology", "")
            authors = proposal.get("authors")
            year = proposal.get("year")

    if not title and not abstract:
        raise HTTPException(400, "Provide either proposal_id or (title + abstract)")

    quality = quality_predictor.predict_quality(title, abstract, authors, year)
    topic = topic_classifier.classify(f"{title} {abstract}")

    response = QualityScoreResponse(
        proposal_id=req.proposal_id,
        overall_score=quality["overall_score"],
        originality_score=quality["originality_score"],
        citation_impact_score=quality["citation_impact_score"],
        methodology_score=quality["methodology_score"],
        clarity_score=quality["clarity_score"],
        topic=topic,
        breakdown={
            "weights": WEIGHTS,
            "features": quality["features"],
        },
        recommendations=quality["recommendations"],
        model_version=quality.get("model_version", "unknown"),
    )

    if req.proposal_id:
        _store_score(req.proposal_id, req.user_id, response.model_dump())

    return response
