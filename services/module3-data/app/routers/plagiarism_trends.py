"""Aggregate plagiarism trends across student cohorts."""

from __future__ import annotations

import logging
from collections import defaultdict

from fastapi import APIRouter, Query
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger(__name__)


class TrendEntry(BaseModel):
    cohort_year: int
    topic_area: str
    avg_similarity: float
    max_similarity: float
    trend_direction: str


class TrendsResponse(BaseModel):
    trends: list[TrendEntry]


@router.get("/plagiarism-trends", response_model=TrendsResponse)
async def get_trends(
    year_from: int = Query(2020, description="Start year"),
    year_to: int = Query(2026, description="End year"),
) -> TrendsResponse:
    """Return aggregated plagiarism trends by cohort and topic.

    1. Query plagiarism_trends table
    2. Aggregate by year + topic
    3. Compute trend direction from consecutive year comparisons
    """
    try:
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "shared"))
        from services.shared.supabase_client import get_supabase_admin
    except ImportError:
        try:
            from shared.supabase_client import get_supabase_admin
        except ImportError:
            return TrendsResponse(trends=[])

    try:
        sb = get_supabase_admin()
        result = sb.table("plagiarism_trends") \
            .select("*") \
            .gte("cohort_year", year_from) \
            .lte("cohort_year", year_to) \
            .order("cohort_year") \
            .execute()
        rows = result.data or []
    except Exception as e:
        logger.warning("Failed to fetch plagiarism trends: %s", e)
        rows = []

    if not rows:
        return TrendsResponse(trends=[])

    # Aggregate by (year, topic)
    grouped: dict[tuple, list] = defaultdict(list)
    for row in rows:
        key = (row.get("cohort_year", 0), row.get("topic_area", "unknown"))
        grouped[key].append(float(row.get("similarity_score", 0)))

    # Compute trends
    topic_year_avg: dict[str, dict[int, float]] = defaultdict(dict)
    trends = []

    for (year, topic), scores in sorted(grouped.items()):
        avg_sim = sum(scores) / len(scores)
        max_sim = max(scores)
        topic_year_avg[topic][year] = avg_sim

        # Direction based on previous year
        prev_avg = topic_year_avg[topic].get(year - 1)
        if prev_avg is not None:
            if avg_sim > prev_avg + 0.02:
                direction = "increasing"
            elif avg_sim < prev_avg - 0.02:
                direction = "decreasing"
            else:
                direction = "stable"
        else:
            direction = "baseline"

        trends.append(TrendEntry(
            cohort_year=year,
            topic_area=topic,
            avg_similarity=round(avg_sim, 4),
            max_similarity=round(max_sim, 4),
            trend_direction=direction,
        ))

    return TrendsResponse(trends=trends)
