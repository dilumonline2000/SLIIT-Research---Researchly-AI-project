"""Real-time dashboard aggregation endpoint."""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class DashboardSnapshot(BaseModel):
    total_proposals: int
    avg_quality_score: float
    top_trending_topics: list[str]
    at_risk_projects: int
    active_supervisors: int


@router.get("/dashboard", response_model=DashboardSnapshot)
async def dashboard() -> DashboardSnapshot:
    """Aggregate cross-module KPIs for the dashboard view.

    TODO (Phase 4): Query Supabase for proposals/quality/predictions,
    subscribe to realtime updates for live refresh.
    """
    return DashboardSnapshot(
        total_proposals=0,
        avg_quality_score=0.0,
        top_trending_topics=[],
        at_risk_projects=0,
        active_supervisors=0,
    )
