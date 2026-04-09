"""Trend forecasting endpoint — ARIMA + Prophet ensemble."""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class TrendForecastPoint(BaseModel):
    date: str
    predicted: float
    lower_bound: float
    upper_bound: float


class TrendForecast(BaseModel):
    topic: str
    model_type: str  # arima | prophet | ensemble
    horizon_months: int
    points: list[TrendForecastPoint]
    mape: float | None = None
    directional_accuracy: float | None = None


class TrendsResponse(BaseModel):
    forecasts: list[TrendForecast]


@router.get("/trends", response_model=TrendsResponse)
async def get_trends() -> TrendsResponse:
    """Return current trend forecasts.

    TODO (Phase 3/4): Query trend_forecasts table, or compute on-demand:
    fit ARIMA + Prophet on topic frequency time series, ensemble by validation MAPE,
    target MAPE < 22% and directional accuracy > 75%.
    """
    return TrendsResponse(forecasts=[])
