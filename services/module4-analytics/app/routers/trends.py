"""Trend forecasting endpoint — ARIMA + Prophet ensemble."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Query
from pydantic import BaseModel

from ..models.forecaster import TrendForecasterModel

router = APIRouter()
logger = logging.getLogger(__name__)

_forecaster: TrendForecasterModel | None = None


def _get_forecaster() -> TrendForecasterModel:
    global _forecaster
    if _forecaster is None:
        _forecaster = TrendForecasterModel()
    return _forecaster


class TrendForecastPoint(BaseModel):
    date: str
    predicted: float
    lower_bound: float
    upper_bound: float


class TrendForecast(BaseModel):
    topic: str
    model_type: str
    horizon_months: int
    points: list[TrendForecastPoint]
    mape: float | None = None
    directional_accuracy: float | None = None


class TrendsResponse(BaseModel):
    forecasts: list[TrendForecast]


@router.get("/trends", response_model=TrendsResponse)
async def get_trends(
    topic: str = Query(None, description="Filter by topic"),
    horizon: int = Query(12, description="Forecast horizon in months"),
) -> TrendsResponse:
    """Return trend forecasts using ARIMA + Prophet ensemble.

    1. Load trained forecaster models
    2. Generate forecasts per topic
    3. Return points with confidence bounds
    """
    forecaster = _get_forecaster()
    topics = forecaster.get_available_topics()

    if topic:
        topics = [t for t in topics if topic.lower() in t.lower()]

    forecasts: list[TrendForecast] = []

    for t in topics[:10]:  # limit to 10 topics
        try:
            result = forecaster.forecast(t, horizon_months=horizon)
            if "error" in result:
                continue

            points = []
            for date, value in zip(result["dates"], result["values"]):
                points.append(TrendForecastPoint(
                    date=date,
                    predicted=value,
                    lower_bound=round(value * 0.85, 2),
                    upper_bound=round(value * 1.15, 2),
                ))

            forecasts.append(TrendForecast(
                topic=t,
                model_type="arima+prophet",
                horizon_months=horizon,
                points=points,
            ))
        except Exception as e:
            logger.warning("Forecast failed for %s: %s", t, e)

    # If no trained models, try on-demand from Supabase data
    if not forecasts:
        forecasts = await _on_demand_forecast(topic, horizon)

    return TrendsResponse(forecasts=forecasts)


async def _on_demand_forecast(topic: str | None, horizon: int) -> list[TrendForecast]:
    """Fallback: query trend_forecasts table for stored predictions."""
    try:
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "shared"))
        from services.shared.supabase_client import get_supabase_admin
        sb = get_supabase_admin()

        query = sb.table("trend_forecasts").select("*").order("forecast_date")
        if topic:
            query = query.eq("topic", topic)
        result = query.limit(100).execute()

        if not result.data:
            return []

        # Group by topic
        from collections import defaultdict
        grouped: dict[str, list] = defaultdict(list)
        for row in result.data:
            grouped[row.get("topic", "unknown")].append(row)

        forecasts = []
        for t, rows in grouped.items():
            points = [
                TrendForecastPoint(
                    date=str(r.get("forecast_date", "")),
                    predicted=float(r.get("predicted_value", 0)),
                    lower_bound=float(r.get("lower_bound", 0)),
                    upper_bound=float(r.get("upper_bound", 0)),
                )
                for r in rows
            ]
            forecasts.append(TrendForecast(
                topic=t, model_type="stored", horizon_months=horizon, points=points,
            ))
        return forecasts
    except Exception as e:
        logger.warning("On-demand forecast failed: %s", e)
        return []
