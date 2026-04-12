"""Quality scoring endpoint — weighted multi-dimensional evaluation."""

from __future__ import annotations

import logging

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()
logger = logging.getLogger(__name__)


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


# Weights from spec
WEIGHTS = {
    "originality": 0.30,
    "citation_impact": 0.25,
    "methodology": 0.25,
    "clarity": 0.20,
}


@router.post("/quality-score", response_model=QualityScoreResponse)
async def quality_score(req: QualityScoreRequest) -> QualityScoreResponse:
    """Compute weighted multi-dimensional quality score.

    1. Fetch proposal from Supabase
    2. Originality: inverse of plagiarism similarity score (30%)
    3. Citation impact: citation count + reference quality (25%)
    4. Methodology: keyword detection for methodology patterns (25%)
    5. Clarity: readability metrics (20%)
    """
    try:
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "shared"))
        from services.shared.supabase_client import get_supabase_admin
    except ImportError:
        try:
            from shared.supabase_client import get_supabase_admin
        except ImportError:
            return _empty_response(req.proposal_id)

    try:
        sb = get_supabase_admin()
        result = sb.table("research_proposals").select("*").eq("id", req.proposal_id).single().execute()
        proposal = result.data
    except Exception as e:
        logger.warning("Failed to fetch proposal: %s", e)
        return _empty_response(req.proposal_id)

    if not proposal:
        return _empty_response(req.proposal_id)

    text = f"{proposal.get('title', '')} {proposal.get('abstract', '')} {proposal.get('methodology', '')}"

    # Originality score (inverse plagiarism)
    plag_score = float(proposal.get("plagiarism_score") or 0)
    originality = max(0, 1.0 - plag_score)

    # Citation impact
    citations = proposal.get("citations") or []
    citation_count = len(citations) if isinstance(citations, list) else 0
    citation_impact = min(1.0, citation_count / 20.0)  # normalize: 20 refs = perfect

    # Methodology detection
    methodology_keywords = [
        "experiment", "survey", "case study", "simulation", "prototype",
        "evaluation", "benchmark", "dataset", "statistical", "hypothesis",
        "mixed method", "qualitative", "quantitative", "systematic review",
    ]
    text_lower = text.lower()
    method_hits = sum(1 for kw in methodology_keywords if kw in text_lower)
    methodology = min(1.0, method_hits / 5.0)

    # Clarity (simple readability proxy)
    words = text.split()
    word_count = len(words)
    if word_count > 0:
        avg_word_len = sum(len(w) for w in words) / word_count
        sentences = text.count(".") + text.count("!") + text.count("?")
        avg_sent_len = word_count / max(sentences, 1)
        # Penalize overly long sentences and overly complex words
        clarity = max(0, min(1.0, 1.0 - (avg_sent_len - 15) / 30 - (avg_word_len - 5) / 10))
    else:
        clarity = 0.0

    # Weighted overall
    overall = (
        originality * WEIGHTS["originality"] +
        citation_impact * WEIGHTS["citation_impact"] +
        methodology * WEIGHTS["methodology"] +
        clarity * WEIGHTS["clarity"]
    )

    # Store score
    try:
        sb.table("quality_scores").upsert({
            "proposal_id": req.proposal_id,
            "user_id": req.user_id,
            "overall_score": round(overall, 4),
            "originality_score": round(originality, 4),
            "citation_impact_score": round(citation_impact, 4),
            "methodology_score": round(methodology, 4),
            "clarity_score": round(clarity, 4),
        }).execute()
    except Exception as e:
        logger.warning("Failed to store quality score: %s", e)

    return QualityScoreResponse(
        proposal_id=req.proposal_id,
        overall_score=round(overall, 4),
        originality_score=round(originality, 4),
        citation_impact_score=round(citation_impact, 4),
        methodology_score=round(methodology, 4),
        clarity_score=round(clarity, 4),
        breakdown={
            "weights": WEIGHTS,
            "word_count": word_count,
            "citation_count": citation_count,
            "methodology_keywords_found": method_hits,
        },
    )


def _empty_response(proposal_id: str) -> QualityScoreResponse:
    return QualityScoreResponse(
        proposal_id=proposal_id, overall_score=0.0,
        originality_score=0.0, citation_impact_score=0.0,
        methodology_score=0.0, clarity_score=0.0, breakdown={},
    )
