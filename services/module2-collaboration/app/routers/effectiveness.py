"""Supervisor effectiveness — list + details.

Endpoints
---------
  GET /effectiveness                        – list every supervisor with summary stats
  GET /effectiveness/by-key?supervisor_key= – full effectiveness for one supervisor
  GET /effectiveness/{supervisor_id}        – legacy: by system uuid
"""

from __future__ import annotations

import logging
import os
import sys
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger(__name__)

_services_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, _services_root)


# ─── Schemas ──────────────────────────────────────────────────────────────


class SupervisorSummary(BaseModel):
    key: str
    source: str            # "sliit" | "system"
    name: str
    email: Optional[str] = None
    department: Optional[str] = None
    research_areas: list[str] = []
    research_cluster: Optional[str] = None
    rank: Optional[str] = None
    level: Optional[str] = None
    availability: Optional[bool] = None
    current_students: Optional[int] = None
    max_students: Optional[int] = None
    avg_stars: Optional[float] = None
    n_ratings: int = 0
    overall_score: Optional[float] = None       # blended 0..1


class SupervisorListResponse(BaseModel):
    supervisors: list[SupervisorSummary]
    total: int


class EffectivenessDetail(BaseModel):
    supervisor: SupervisorSummary
    overall_score: float
    completion_rate: float
    avg_feedback_sentiment: float
    student_satisfaction: float
    avg_stars: Optional[float] = None
    n_ratings: int = 0
    breakdown: dict
    recent_feedback: list[dict] = []


# ─── Helpers ──────────────────────────────────────────────────────────────


def _supabase():
    try:
        from shared.supabase_client import get_supabase_admin
        return get_supabase_admin()
    except Exception as e:
        logger.error("Supabase admin client unavailable: %s", e)
        return None


def _aggregate_ratings(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {"avg_stars": None, "avg_sentiment": None, "n_ratings": 0, "satisfaction": None}
    stars = [int(r.get("stars") or 0) for r in rows if r.get("stars") is not None]
    sents = [float(r.get("sentiment_score")) for r in rows if r.get("sentiment_score") is not None]
    avg_stars = sum(stars) / len(stars) if stars else None
    avg_sent = sum(sents) / len(sents) if sents else None
    pos = sum(1 for s in sents if s > 0.3)
    satisfaction = pos / len(sents) if sents else None
    return {
        "avg_stars": avg_stars,
        "avg_sentiment": avg_sent,
        "n_ratings": len(rows),
        "satisfaction": satisfaction,
    }


def _blend_score(avg_stars: Optional[float], avg_sentiment: Optional[float],
                  satisfaction: Optional[float], completion_rate: float) -> float:
    """Combine signals into a single 0..1 effectiveness score.

    Components (always normalised to 0..1):
      - star score   = avg_stars / 5
      - sentiment    = (avg_sentiment + 1) / 2
      - satisfaction = satisfaction (already 0..1)
      - completion   = completion_rate
    """
    star_norm = (avg_stars / 5.0) if avg_stars is not None else None
    sent_norm = ((avg_sentiment + 1) / 2) if avg_sentiment is not None else None

    parts: list[tuple[float, float]] = []  # (weight, value)
    if star_norm is not None:    parts.append((0.40, star_norm))
    if sent_norm is not None:    parts.append((0.25, sent_norm))
    if satisfaction is not None: parts.append((0.15, satisfaction))
    parts.append((0.20, completion_rate))

    total_w = sum(w for w, _ in parts)
    if total_w <= 0:
        return 0.0
    score = sum(w * v for w, v in parts) / total_w
    return round(max(0.0, min(1.0, score)), 3)


def _ratings_for_key(sb, key: str) -> list[dict[str, Any]]:
    if not sb or ":" not in key:
        return []
    src, ident = key.split(":", 1)
    try:
        q = sb.table("supervisor_ratings").select("*")
        if src == "sliit":
            q = q.eq("sliit_supervisor_id", int(ident))
        else:
            q = q.eq("system_supervisor_id", ident)
        return (q.execute().data) or []
    except Exception as e:
        logger.warning("Could not fetch ratings for %s: %s", key, e)
        return []


def _completion_rate_for_system(sb, supervisor_uuid: str) -> tuple[float, dict]:
    if not sb:
        return 0.0, {}
    try:
        res = sb.table("supervisor_matches").select("status").eq("supervisor_id", supervisor_uuid).execute()
        rows = res.data or []
    except Exception:
        rows = []
    total = len(rows)
    completed = sum(1 for r in rows if r.get("status") == "completed")
    rate = completed / max(total, 1)
    return rate, {"total_students": total, "completed": completed}


# ─── Endpoints ────────────────────────────────────────────────────────────


@router.get("", response_model=SupervisorListResponse)
async def list_effectiveness(limit: int = Query(default=200, le=500)) -> SupervisorListResponse:
    """List every supervisor with their aggregate stats. Used by the
    Effectiveness dashboard to show a sortable table."""
    from app.services.supervisor_directory import list_all
    sb = _supabase()
    items = list_all()[:limit]

    out: list[SupervisorSummary] = []
    for it in items:
        ratings = _ratings_for_key(sb, it["key"])
        agg = _aggregate_ratings(ratings)
        completion = 0.0
        if it["source"] == "system":
            completion, _ = _completion_rate_for_system(sb, str(it["id"]))
        score = _blend_score(agg["avg_stars"], agg["avg_sentiment"], agg["satisfaction"], completion)
        out.append(SupervisorSummary(
            key=it["key"], source=it["source"], name=it["name"],
            email=it.get("email"), department=it.get("department"),
            research_areas=it.get("research_areas") or [],
            research_cluster=it.get("research_cluster"),
            rank=it.get("rank"), level=it.get("level"),
            availability=it.get("availability"),
            current_students=it.get("current_students"),
            max_students=it.get("max_students"),
            avg_stars=round(agg["avg_stars"], 2) if agg["avg_stars"] is not None else None,
            n_ratings=agg["n_ratings"],
            overall_score=score,
        ))
    out.sort(key=lambda s: (s.overall_score or 0, s.n_ratings), reverse=True)
    return SupervisorListResponse(supervisors=out, total=len(out))


@router.get("/by-key", response_model=EffectivenessDetail)
async def effectiveness_by_key(
    supervisor_key: str = Query(..., description="'sliit:<id>' or 'system:<uuid>'"),
) -> EffectivenessDetail:
    """Full effectiveness profile for one supervisor."""
    from app.services.supervisor_directory import get_one
    sup = get_one(supervisor_key)
    if not sup:
        raise HTTPException(status_code=404, detail="Supervisor not found")

    sb = _supabase()
    ratings = _ratings_for_key(sb, supervisor_key)
    agg = _aggregate_ratings(ratings)

    completion, breakdown = 0.0, {}
    if sup["source"] == "system":
        completion, breakdown = _completion_rate_for_system(sb, str(sup["id"]))

    score = _blend_score(agg["avg_stars"], agg["avg_sentiment"], agg["satisfaction"], completion)
    summary = SupervisorSummary(
        key=sup["key"], source=sup["source"], name=sup["name"],
        email=sup.get("email"), department=sup.get("department"),
        research_areas=sup.get("research_areas") or [],
        research_cluster=sup.get("research_cluster"),
        rank=sup.get("rank"), level=sup.get("level"),
        availability=sup.get("availability"),
        current_students=sup.get("current_students"),
        max_students=sup.get("max_students"),
        avg_stars=round(agg["avg_stars"], 2) if agg["avg_stars"] is not None else None,
        n_ratings=agg["n_ratings"],
        overall_score=score,
    )

    recent = [
        {
            "id": str(r.get("id", "")),
            "stars": int(r.get("stars") or 0),
            "feedback_text": r.get("feedback_text"),
            "overall_sentiment": r.get("overall_sentiment"),
            "sentiment_score": r.get("sentiment_score"),
            "rater_name": r.get("rater_name"),
            "created_at": r.get("created_at"),
        }
        for r in ratings[:10]
    ]

    return EffectivenessDetail(
        supervisor=summary,
        overall_score=score,
        completion_rate=round(completion, 3),
        avg_feedback_sentiment=round(agg["avg_sentiment"], 3) if agg["avg_sentiment"] is not None else 0.0,
        student_satisfaction=round(agg["satisfaction"], 3) if agg["satisfaction"] is not None else 0.0,
        avg_stars=round(agg["avg_stars"], 2) if agg["avg_stars"] is not None else None,
        n_ratings=agg["n_ratings"],
        breakdown={
            **breakdown,
            "n_ratings": agg["n_ratings"],
            "weights": {"stars": 0.40, "sentiment": 0.25, "satisfaction": 0.15, "completion": 0.20},
        },
        recent_feedback=recent,
    )


# Legacy endpoint kept for backwards compat
class LegacyEffectivenessResponse(BaseModel):
    supervisor_id: str
    overall_score: float
    completion_rate: float
    avg_feedback_sentiment: float
    student_satisfaction: float
    breakdown: dict


@router.get("/{supervisor_id}", response_model=LegacyEffectivenessResponse)
async def get_effectiveness(supervisor_id: str) -> LegacyEffectivenessResponse:
    """Legacy: compute effectiveness by raw system supervisor uuid."""
    sb = _supabase()
    completion, breakdown = _completion_rate_for_system(sb, supervisor_id)
    ratings = _ratings_for_key(sb, f"system:{supervisor_id}") if sb else []
    agg = _aggregate_ratings(ratings)
    score = _blend_score(agg["avg_stars"], agg["avg_sentiment"], agg["satisfaction"], completion)
    return LegacyEffectivenessResponse(
        supervisor_id=supervisor_id,
        overall_score=score,
        completion_rate=round(completion, 3),
        avg_feedback_sentiment=round(agg["avg_sentiment"], 3) if agg["avg_sentiment"] is not None else 0.0,
        student_satisfaction=round(agg["satisfaction"], 3) if agg["satisfaction"] is not None else 0.0,
        breakdown={
            **breakdown,
            "n_ratings": agg["n_ratings"],
            "weights": {"stars": 0.40, "sentiment": 0.25, "satisfaction": 0.15, "completion": 0.20},
        },
    )
