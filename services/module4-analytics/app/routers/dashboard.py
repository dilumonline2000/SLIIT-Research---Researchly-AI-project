"""Real-time dashboard aggregation endpoint."""

from __future__ import annotations

import logging

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger(__name__)


class DashboardSnapshot(BaseModel):
    total_proposals: int
    avg_quality_score: float
    top_trending_topics: list[str]
    at_risk_projects: int
    active_supervisors: int


@router.get("/dashboard", response_model=DashboardSnapshot)
async def dashboard() -> DashboardSnapshot:
    """Aggregate cross-module KPIs for the dashboard view.

    Queries multiple Supabase tables and aggregates metrics.
    """
    try:
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "shared"))
        from services.shared.supabase_client import get_supabase_admin
    except ImportError:
        try:
            from shared.supabase_client import get_supabase_admin
        except ImportError:
            return DashboardSnapshot(
                total_proposals=0, avg_quality_score=0.0,
                top_trending_topics=[], at_risk_projects=0, active_supervisors=0,
            )

    sb = get_supabase_admin()

    # Total proposals
    try:
        proposals_result = sb.table("research_proposals").select("id", count="exact").execute()
        total_proposals = proposals_result.count or 0
    except Exception:
        total_proposals = 0

    # Average quality score
    try:
        quality_result = sb.table("quality_scores").select("overall_score").execute()
        scores = [float(r["overall_score"]) for r in (quality_result.data or []) if r.get("overall_score")]
        avg_quality = sum(scores) / len(scores) if scores else 0.0
    except Exception:
        avg_quality = 0.0

    # Trending topics from research_papers keywords
    try:
        papers_result = sb.table("research_papers").select("keywords").limit(500).execute()
        from collections import Counter
        topic_counter: Counter = Counter()
        for p in (papers_result.data or []):
            for kw in (p.get("keywords") or []):
                topic_counter[kw] += 1
        top_topics = [t for t, _ in topic_counter.most_common(5)]
    except Exception:
        top_topics = []

    # At-risk projects (success predictions < 0.5)
    try:
        predictions_result = sb.table("success_predictions").select("success_probability").execute()
        at_risk = sum(1 for r in (predictions_result.data or []) if float(r.get("success_probability", 1)) < 0.5)
    except Exception:
        at_risk = 0

    # Active supervisors
    try:
        supervisors_result = sb.table("supervisor_matches") \
            .select("supervisor_id") \
            .eq("status", "active") \
            .execute()
        active_ids = set(r["supervisor_id"] for r in (supervisors_result.data or []) if r.get("supervisor_id"))
        active_supervisors = len(active_ids)
    except Exception:
        active_supervisors = 0

    return DashboardSnapshot(
        total_proposals=total_proposals,
        avg_quality_score=round(avg_quality, 3),
        top_trending_topics=top_topics,
        at_risk_projects=at_risk,
        active_supervisors=active_supervisors,
    )
