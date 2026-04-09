"""Aggregate plagiarism trends across student cohorts."""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class TrendEntry(BaseModel):
    cohort_year: int
    topic_area: str
    avg_similarity: float
    max_similarity: float
    trend_direction: str


class TrendsResponse(BaseModel):
    trends: list[TrendEntry]


@router.get("/trends", response_model=TrendsResponse)
async def get_trends() -> TrendsResponse:
    """Return aggregated plagiarism trends by cohort.

    TODO (Phase 4): Query plagiarism_trends table, aggregate by year + topic,
    compute trend direction from time series.
    """
    return TrendsResponse(trends=[])
