"""Trend forecasting endpoint — uses trained ARIMA models on SLIIT publication data."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Query
from pydantic import BaseModel

from ..services import trend_forecaster

router = APIRouter()
logger = logging.getLogger(__name__)


class TrendPoint(BaseModel):
    year: int
    count: float
    type: str  # "historical" or "forecast"


class TrendForecast(BaseModel):
    topic: str
    horizon_years: int
    historical: list[TrendPoint]
    forecast: list[TrendPoint]
    trend_direction: str
    model_type: str
    data_range: str
    model_version: str


class TrendsResponse(BaseModel):
    forecasts: list[TrendForecast]
    available_topics: list[str]


@router.get("/trends", response_model=TrendsResponse)
async def get_trends(
    topic: str = Query(None, description="Specific topic (e.g. 'computing', 'business')"),
    horizon: int = Query(3, ge=1, le=10, description="Forecast horizon in years"),
) -> TrendsResponse:
    """Return trend forecasts using trained ARIMA models on SLIIT publication data."""
    available = trend_forecaster.get_available_topics()

    if topic:
        topics_to_forecast = [t for t in available if topic.lower() in t.lower()]
        if not topics_to_forecast:
            topics_to_forecast = ["all"] if "all" in available else available[:1]
    else:
        # Default: return forecasts for all main topics (skip "all" aggregate)
        topics_to_forecast = [t for t in available if t != "all"]

    forecasts: list[TrendForecast] = []
    for t in topics_to_forecast:
        try:
            result = trend_forecaster.forecast(t, horizon=horizon)
            forecasts.append(TrendForecast(**result))
        except Exception as e:
            logger.warning("Forecast failed for %s: %s", t, e)

    return TrendsResponse(forecasts=forecasts, available_topics=available)
