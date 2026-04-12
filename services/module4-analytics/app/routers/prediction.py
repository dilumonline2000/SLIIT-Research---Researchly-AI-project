"""Success prediction endpoint — RF + XGBoost ensemble."""

from __future__ import annotations

import logging
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from ..models.success_predictor import SuccessPredictorModel

router = APIRouter()
logger = logging.getLogger(__name__)

_predictor: SuccessPredictorModel | None = None


def _get_predictor() -> SuccessPredictorModel:
    global _predictor
    if _predictor is None:
        _predictor = SuccessPredictorModel()
    return _predictor


class PredictRequest(BaseModel):
    proposal_id: str
    user_id: str


class RiskFactor(BaseModel):
    factor: str
    severity: Literal["low", "medium", "high", "critical"]
    description: str


class PredictResponse(BaseModel):
    proposal_id: str
    success_probability: float
    risk_level: Literal["low", "medium", "high", "critical"]
    risk_factors: list[RiskFactor]
    recommendations: list[str]
    model_type: str


@router.post("/predict", response_model=PredictResponse)
async def predict(req: PredictRequest) -> PredictResponse:
    """Run RF + XGBoost soft-voting ensemble to predict success likelihood.

    1. Fetch student progress features from Supabase
    2. Run through the trained ensemble model
    3. Generate risk factors and recommendations
    """
    try:
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "shared"))
        from services.shared.supabase_client import get_supabase_admin
    except ImportError:
        try:
            from shared.supabase_client import get_supabase_admin
        except ImportError:
            return _fallback_response(req.proposal_id)

    sb = get_supabase_admin()

    # Fetch student progress features
    features = await _gather_features(sb, req.user_id, req.proposal_id)

    # Run prediction
    predictor = _get_predictor()
    try:
        result = predictor.predict(features)
    except Exception as e:
        logger.error("Prediction failed: %s", e)
        return _fallback_response(req.proposal_id)

    if "error" in result:
        return _fallback_response(req.proposal_id)

    probability = result["probability"]

    # Risk level
    if probability >= 0.75:
        risk_level = "low"
    elif probability >= 0.5:
        risk_level = "medium"
    elif probability >= 0.25:
        risk_level = "high"
    else:
        risk_level = "critical"

    # Convert risk factors
    risk_factors = []
    for rf in result.get("risk_factors", []):
        severity = "high" if rf.get("value", 0) > 30 else "medium"
        risk_factors.append(RiskFactor(
            factor=rf["factor"],
            severity=severity,
            description=rf.get("concern", ""),
        ))

    # Generate recommendations
    recommendations = _generate_recommendations(features, probability, risk_factors)

    # Store prediction
    try:
        sb.table("success_predictions").upsert({
            "proposal_id": req.proposal_id,
            "user_id": req.user_id,
            "success_probability": probability,
            "risk_level": risk_level,
            "model_type": "rf+xgboost-v1",
        }).execute()
    except Exception as e:
        logger.warning("Failed to store prediction: %s", e)

    return PredictResponse(
        proposal_id=req.proposal_id,
        success_probability=round(probability, 4),
        risk_level=risk_level,
        risk_factors=risk_factors,
        recommendations=recommendations,
        model_type="rf+xgboost-v1",
    )


async def _gather_features(sb, user_id: str, proposal_id: str) -> dict[str, float]:
    """Gather the 10 prediction features from various Supabase tables."""
    features = {
        "milestone_completion_rate": 0.5,
        "login_frequency": 3.0,
        "submission_frequency": 1.5,
        "quality_score_trajectory": 0.0,
        "supervisor_interaction_frequency": 1.0,
        "topic_trend_alignment": 0.5,
        "peer_collaboration_score": 0.3,
        "citation_count": 5.0,
        "feedback_sentiment_avg": 0.0,
        "days_since_last_submission": 14.0,
    }

    try:
        # Quality scores
        quality_result = sb.table("quality_scores") \
            .select("overall_score") \
            .eq("user_id", user_id) \
            .order("created_at", desc=True) \
            .limit(5).execute()
        scores = [float(r["overall_score"]) for r in (quality_result.data or []) if r.get("overall_score")]
        if len(scores) >= 2:
            features["quality_score_trajectory"] = scores[0] - scores[-1]
        if scores:
            features["milestone_completion_rate"] = scores[0]
    except Exception:
        pass

    try:
        # Feedback sentiment
        feedback_result = sb.table("feedback_entries") \
            .select("sentiment_score") \
            .eq("student_id", user_id).execute()
        sentiments = [float(r["sentiment_score"]) for r in (feedback_result.data or []) if r.get("sentiment_score") is not None]
        if sentiments:
            features["feedback_sentiment_avg"] = sum(sentiments) / len(sentiments)
    except Exception:
        pass

    try:
        # Citation count from proposal
        proposal_result = sb.table("research_proposals") \
            .select("citations") \
            .eq("id", proposal_id).single().execute()
        if proposal_result.data:
            citations = proposal_result.data.get("citations") or []
            features["citation_count"] = float(len(citations)) if isinstance(citations, list) else 0.0
    except Exception:
        pass

    try:
        # Supervisor interactions
        match_result = sb.table("supervisor_matches") \
            .select("id") \
            .eq("student_id", user_id) \
            .eq("status", "active").execute()
        features["supervisor_interaction_frequency"] = float(len(match_result.data or []))
    except Exception:
        pass

    return features


def _generate_recommendations(features: dict, probability: float, risk_factors: list[RiskFactor]) -> list[str]:
    """Generate actionable recommendations based on risk factors."""
    recs = []
    if features.get("days_since_last_submission", 0) > 21:
        recs.append("Submit a progress update — your last submission was over 3 weeks ago.")
    if features.get("supervisor_interaction_frequency", 0) < 1:
        recs.append("Schedule a meeting with your supervisor to discuss progress.")
    if features.get("citation_count", 0) < 5:
        recs.append("Strengthen your literature review — aim for at least 10 quality references.")
    if features.get("quality_score_trajectory", 0) < 0:
        recs.append("Your quality scores are declining — review feedback and revise accordingly.")
    if features.get("peer_collaboration_score", 0) < 0.3:
        recs.append("Connect with peers in your research area for feedback and collaboration.")
    if probability < 0.5 and not recs:
        recs.append("Consider revising your research scope or methodology to improve feasibility.")
    return recs


def _fallback_response(proposal_id: str) -> PredictResponse:
    return PredictResponse(
        proposal_id=proposal_id, success_probability=0.5,
        risk_level="medium", risk_factors=[], recommendations=[],
        model_type="fallback",
    )
