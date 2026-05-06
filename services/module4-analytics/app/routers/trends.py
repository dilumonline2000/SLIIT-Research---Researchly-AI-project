"""Trend forecasting endpoints — uses trained ARIMA models on SLIIT publication data.

Endpoints
---------
  GET  /trends                  – per-topic forecasts (with CI + accuracy metrics)
  POST /trends/compare          – multi-topic comparison data (overlapping series)
  GET  /trends/insights         – emerging topics + predictive recommendations
  POST /trends/report           – HTML report (download)
  GET  /trends/topics           – list available topics
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from ..services import trend_forecaster

router = APIRouter()
logger = logging.getLogger(__name__)


# ─── Schemas ──────────────────────────────────────────────────────────────


class HistoricalPoint(BaseModel):
    year: int
    count: float
    type: str = "historical"


class ForecastPoint(BaseModel):
    year: int
    count: float
    lower: float = 0.0
    upper: float = 0.0
    type: str = "forecast"


class Accuracy(BaseModel):
    available: bool = False
    rmse: float = 0.0
    mae: float = 0.0
    nrmse: float = 0.0
    n_observations: int = 0


class TrendStats(BaseModel):
    historical_total: Optional[int] = None
    historical_peak: Optional[dict[str, Any]] = None
    current_count: Optional[int] = None
    forecast_end: Optional[float] = None


class TrendForecast(BaseModel):
    topic: str
    horizon_years: int
    historical: list[HistoricalPoint]
    forecast: list[ForecastPoint]
    trend_direction: str
    growth_pct: float = 0.0
    interpretation: str = ""
    accuracy: Accuracy = Accuracy()
    model_type: str
    data_range: str
    model_version: str
    stats: TrendStats = TrendStats()


class TrendsResponse(BaseModel):
    forecasts: list[TrendForecast]
    available_topics: list[str]


class CompareRequest(BaseModel):
    topics: list[str] = Field(..., min_length=1, max_length=8)
    horizon: int = Field(3, ge=1, le=10)


class CompareResponse(BaseModel):
    forecasts: list[TrendForecast]
    ranking: list[dict[str, Any]]   # sorted by growth_pct, fastest growing first
    horizon: int


class EmergingTopic(BaseModel):
    topic: str
    score: float
    recent_slope: float
    long_term_slope: float
    latest_count: int
    growth_ratio: float
    growth_pct: float = 0.0
    interpretation: str


class Recommendation(BaseModel):
    topic: str
    score: float
    growth_pct: float
    latest_count: int
    saturation: float
    rationale: str
    suggested_title: str


class InsightsResponse(BaseModel):
    horizon: int
    emerging: list[EmergingTopic]
    recommendations: list[Recommendation]
    model_version: str = "unknown"


class ReportRequest(BaseModel):
    payload: dict[str, Any]


# ─── Endpoints ────────────────────────────────────────────────────────────


@router.get("/trends", response_model=TrendsResponse)
async def get_trends(
    topic: str = Query(None, description="Specific topic substring (e.g. 'computing')"),
    horizon: int = Query(3, ge=1, le=10, description="Forecast horizon in years"),
) -> TrendsResponse:
    """Return ARIMA forecasts (with confidence intervals + accuracy) per topic."""
    available = trend_forecaster.get_available_topics()

    if topic:
        topics_to_forecast = [t for t in available if topic.lower() in t.lower()]
        if not topics_to_forecast:
            topics_to_forecast = ["all"] if "all" in available else available[:1]
    else:
        # Default: all topics except the 'all' aggregate (cleaner UX)
        topics_to_forecast = [t for t in available if t != "all"]

    forecasts: list[TrendForecast] = []
    for t in topics_to_forecast:
        try:
            result = trend_forecaster.forecast(t, horizon=horizon)
            forecasts.append(TrendForecast(**result))
        except Exception as e:
            logger.warning("Forecast failed for %s: %s", t, e)

    return TrendsResponse(forecasts=forecasts, available_topics=available)


@router.post("/trends/compare", response_model=CompareResponse)
async def compare_topics(req: CompareRequest) -> CompareResponse:
    """Multi-topic comparison — returns the same shape as /trends plus a growth ranking."""
    forecasts: list[TrendForecast] = []
    for t in req.topics:
        try:
            result = trend_forecaster.forecast(t, horizon=req.horizon)
            forecasts.append(TrendForecast(**result))
        except Exception as e:
            logger.warning("Compare-forecast failed for %s: %s", t, e)

    ranking = sorted(
        [
            {
                "topic": f.topic,
                "growth_pct": f.growth_pct,
                "direction": f.trend_direction,
                "current": f.stats.current_count or 0,
                "forecast_end": f.stats.forecast_end or 0,
            }
            for f in forecasts
        ],
        key=lambda r: r["growth_pct"], reverse=True,
    )
    return CompareResponse(forecasts=forecasts, ranking=ranking, horizon=req.horizon)


@router.get("/trends/insights", response_model=InsightsResponse)
async def trend_insights(
    horizon: int = Query(3, ge=1, le=10),
    top_k: int = Query(5, ge=1, le=10),
) -> InsightsResponse:
    """Surface emerging topics + 'best area to focus' recommendations."""
    emerging = trend_forecaster.emerging_topics(horizon=horizon, top_k=top_k)
    recs = trend_forecaster.recommendations(horizon=horizon, top_k=top_k)
    info = trend_forecaster.get_model_info()
    return InsightsResponse(
        horizon=horizon,
        emerging=[EmergingTopic(**e) for e in emerging],
        recommendations=[Recommendation(**r) for r in recs],
        model_version=info.get("version", "unknown"),
    )


@router.get("/trends/topics")
async def list_topics() -> dict[str, list[str]]:
    return {"topics": trend_forecaster.get_available_topics()}


@router.post("/trends/report", response_class=HTMLResponse)
async def download_report(req: ReportRequest) -> HTMLResponse:
    """Render the analysis as a self-contained HTML report."""
    html = trend_forecaster.generate_report_html(req.payload)
    return HTMLResponse(content=html)
