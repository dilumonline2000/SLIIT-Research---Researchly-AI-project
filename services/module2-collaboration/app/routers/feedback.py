"""Feedback sentiment + supervisor ratings.

Endpoints
---------
  POST /feedback/analyze             – aspect-based sentiment (Gemini)
  GET  /feedback/supervisors         – list every rate-able supervisor (SLIIT + system)
  POST /feedback/submit              – save a rating + (optional) text under a supervisor
  GET  /feedback/by-supervisor       – fetch the saved ratings for one supervisor
"""

from __future__ import annotations

import logging
import os
import sys
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter()
logger = logging.getLogger(__name__)

_services_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, _services_root)


# ─── Schemas ──────────────────────────────────────────────────────────────


class AnalyzeFeedbackRequest(BaseModel):
    feedback_text: str = Field(..., min_length=1)


class AspectSentiment(BaseModel):
    methodology: str
    writing: str
    originality: str
    data_analysis: str


class AnalyzeFeedbackResponse(BaseModel):
    overall_sentiment: str
    overall_score: float
    aspects: AspectSentiment
    aspect_probabilities: dict | None = None


class SupervisorEntry(BaseModel):
    key: str                     # "sliit:1" or "system:<uuid>"
    source: str                  # "sliit" | "system"
    name: str
    email: Optional[str] = None
    department: Optional[str] = None
    research_cluster: Optional[str] = None
    research_areas: list[str] = []
    rank: Optional[str] = None
    level: Optional[str] = None
    availability: Optional[bool] = None


class SupervisorListResponse(BaseModel):
    supervisors: list[SupervisorEntry]
    total: int


class SubmitFeedbackRequest(BaseModel):
    supervisor_key: str = Field(..., description="e.g. 'sliit:1' or 'system:<uuid>'")
    stars: int = Field(..., ge=1, le=5)
    feedback_text: Optional[str] = Field(default=None, max_length=4000)
    rater_id: Optional[str] = None
    rater_name: Optional[str] = None


class SubmitFeedbackResponse(BaseModel):
    rating_id: str
    supervisor_key: str
    stars: int
    overall_sentiment: Optional[str] = None
    overall_score: Optional[float] = None


class RatingEntry(BaseModel):
    id: str
    stars: int
    feedback_text: Optional[str] = None
    overall_sentiment: Optional[str] = None
    sentiment_score: Optional[float] = None
    rater_name: Optional[str] = None
    created_at: Optional[str] = None


class BySupervisorResponse(BaseModel):
    supervisor: Optional[SupervisorEntry] = None
    avg_stars: Optional[float] = None
    avg_sentiment: Optional[float] = None
    n_ratings: int = 0
    ratings: list[RatingEntry] = []


# ─── Helpers ──────────────────────────────────────────────────────────────


def _supabase():
    try:
        from shared.supabase_client import get_supabase_admin
        return get_supabase_admin()
    except Exception as e:
        logger.error("Supabase admin client unavailable: %s", e)
        return None


def _split_supervisor_key(key: str) -> tuple[str, str]:
    if not key or ":" not in key:
        raise HTTPException(status_code=400, detail="supervisor_key must be 'sliit:<id>' or 'system:<uuid>'")
    src, ident = key.split(":", 1)
    if src not in ("sliit", "system"):
        raise HTTPException(status_code=400, detail="supervisor_key source must be 'sliit' or 'system'")
    return src, ident


def _gemini_sentiment(text: str) -> dict[str, Any]:
    """Best-effort sentiment analysis. Falls back to a star-based estimate
    when Gemini is unavailable."""
    try:
        from shared.gemini_client import generate_json

        prompt = f"""Analyze this academic research feedback for sentiment across four aspects.

Feedback: {text}

For each aspect, determine the sentiment: "positive", "neutral", or "negative".
Provide probability scores (must sum to 1.0 per aspect).

Return JSON:
{{
  "methodology": {{"sentiment": "positive", "positive": 0.8, "neutral": 0.15, "negative": 0.05}},
  "writing": {{"sentiment": "neutral", "positive": 0.3, "neutral": 0.5, "negative": 0.2}},
  "originality": {{"sentiment": "positive", "positive": 0.7, "neutral": 0.2, "negative": 0.1}},
  "data_analysis": {{"sentiment": "neutral", "positive": 0.3, "neutral": 0.5, "negative": 0.2}},
  "overall_sentiment": "positive",
  "overall_score": 0.4
}}

overall_score: -1.0 (very negative) to 1.0 (very positive)"""
        data = generate_json(prompt)
        SCORE_MAP = {"positive": 1.0, "neutral": 0.0, "negative": -1.0}
        labels: dict[str, str] = {}
        probs: dict[str, dict[str, float]] = {}
        for aspect in ["methodology", "writing", "originality", "data_analysis"]:
            asp = data.get(aspect, {})
            sentiment = asp.get("sentiment", "neutral")
            labels[aspect] = sentiment
            probs[aspect] = {
                "positive": float(asp.get("positive", 0.33)),
                "neutral":  float(asp.get("neutral",  0.34)),
                "negative": float(asp.get("negative", 0.33)),
            }
        scores = [SCORE_MAP.get(s, 0.0) for s in labels.values()]
        avg = sum(scores) / max(len(scores), 1)
        overall = data.get("overall_sentiment")
        if overall not in ("positive", "neutral", "negative"):
            overall = "positive" if avg > 0.3 else ("negative" if avg < -0.3 else "neutral")
        return {
            "overall_sentiment": overall,
            "overall_score": round(float(data.get("overall_score", avg)), 3),
            "aspect_labels": labels,
            "aspect_probabilities": probs,
        }
    except Exception as e:
        logger.info("Gemini sentiment unavailable, using neutral default: %s", e)
        return {
            "overall_sentiment": "neutral",
            "overall_score": 0.0,
            "aspect_labels": {a: "neutral" for a in ("methodology", "writing", "originality", "data_analysis")},
            "aspect_probabilities": None,
        }


def _stars_to_sentiment(stars: int) -> dict[str, Any]:
    """Heuristic: convert a star rating to a sentiment label/score so the
    record stays useful even when Gemini didn't run."""
    if stars >= 4:
        return {"overall_sentiment": "positive", "overall_score": (stars - 3) / 2}
    if stars <= 2:
        return {"overall_sentiment": "negative", "overall_score": (stars - 3) / 2}
    return {"overall_sentiment": "neutral", "overall_score": 0.0}


# ─── Endpoints ────────────────────────────────────────────────────────────


@router.post("/analyze", response_model=AnalyzeFeedbackResponse)
async def analyze_feedback(req: AnalyzeFeedbackRequest) -> AnalyzeFeedbackResponse:
    """Aspect-based sentiment analysis of a free-text feedback."""
    info = _gemini_sentiment(req.feedback_text)
    return AnalyzeFeedbackResponse(
        overall_sentiment=info["overall_sentiment"],
        overall_score=info["overall_score"],
        aspects=AspectSentiment(**info["aspect_labels"]),
        aspect_probabilities=info["aspect_probabilities"],
    )


@router.get("/supervisors", response_model=SupervisorListResponse)
async def list_supervisors() -> SupervisorListResponse:
    """List every supervisor a student can rate (SLIIT + system supervisors)."""
    from app.services.supervisor_directory import list_all
    items = list_all()
    return SupervisorListResponse(
        supervisors=[SupervisorEntry(**i) for i in items],
        total=len(items),
    )


@router.post("/submit", response_model=SubmitFeedbackResponse)
async def submit_feedback(req: SubmitFeedbackRequest) -> SubmitFeedbackResponse:
    """Save a rating + optional feedback under a supervisor."""
    src, ident = _split_supervisor_key(req.supervisor_key)
    sb = _supabase()
    if sb is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    # Resolve supervisor metadata so we can denormalise sliit info into the row
    from app.services.supervisor_directory import get_one
    sup = get_one(req.supervisor_key)
    if sup is None:
        raise HTTPException(status_code=404, detail="Supervisor not found")

    # Run sentiment if there's text; else infer from stars
    if req.feedback_text and req.feedback_text.strip():
        sent = _gemini_sentiment(req.feedback_text)
    else:
        sent = {**_stars_to_sentiment(req.stars), "aspect_probabilities": None}

    payload: dict[str, Any] = {
        "stars": req.stars,
        "feedback_text": req.feedback_text,
        "overall_sentiment": sent.get("overall_sentiment"),
        "sentiment_score": sent.get("overall_score"),
        "aspect_sentiments": sent.get("aspect_probabilities"),
        "rater_id": req.rater_id,
        "rater_name": req.rater_name,
    }
    if src == "sliit":
        payload["sliit_supervisor_id"] = int(ident)
        payload["sliit_supervisor_name"] = sup.get("name")
        payload["sliit_supervisor_email"] = sup.get("email")
    else:
        payload["system_supervisor_id"] = ident

    try:
        ins = sb.table("supervisor_ratings").insert(payload).execute()
        rows = ins.data or []
        if not rows:
            raise RuntimeError("Insert returned no rows")
        rid = str(rows[0].get("id", ""))
    except Exception as e:
        logger.error("Failed to insert rating: %s", e)
        raise HTTPException(status_code=500, detail=f"Could not save rating: {e}")

    return SubmitFeedbackResponse(
        rating_id=rid,
        supervisor_key=req.supervisor_key,
        stars=req.stars,
        overall_sentiment=sent.get("overall_sentiment"),
        overall_score=sent.get("overall_score"),
    )


@router.get("/by-supervisor", response_model=BySupervisorResponse)
async def by_supervisor(
    supervisor_key: str = Query(..., description="'sliit:<id>' or 'system:<uuid>'"),
    limit: int = Query(default=50, le=200),
) -> BySupervisorResponse:
    """Return supervisor info + saved ratings + aggregate stats."""
    from app.services.supervisor_directory import get_one
    src, ident = _split_supervisor_key(supervisor_key)
    sup = get_one(supervisor_key)

    sb = _supabase()
    rows: list[dict[str, Any]] = []
    if sb is not None:
        try:
            q = sb.table("supervisor_ratings").select("*").order("created_at", desc=True).limit(limit)
            if src == "sliit":
                q = q.eq("sliit_supervisor_id", int(ident))
            else:
                q = q.eq("system_supervisor_id", ident)
            res = q.execute()
            rows = res.data or []
        except Exception as e:
            logger.warning("Could not fetch ratings: %s", e)

    ratings = [
        RatingEntry(
            id=str(r.get("id", "")),
            stars=int(r.get("stars") or 0),
            feedback_text=r.get("feedback_text"),
            overall_sentiment=r.get("overall_sentiment"),
            sentiment_score=r.get("sentiment_score"),
            rater_name=r.get("rater_name"),
            created_at=r.get("created_at"),
        )
        for r in rows
    ]
    avg_stars = (sum(r.stars for r in ratings) / len(ratings)) if ratings else None
    sent_scores = [r.sentiment_score for r in ratings if r.sentiment_score is not None]
    avg_sentiment = (sum(sent_scores) / len(sent_scores)) if sent_scores else None

    return BySupervisorResponse(
        supervisor=SupervisorEntry(**sup) if sup else None,
        avg_stars=round(avg_stars, 2) if avg_stars is not None else None,
        avg_sentiment=round(avg_sentiment, 3) if avg_sentiment is not None else None,
        n_ratings=len(ratings),
        ratings=ratings,
    )
