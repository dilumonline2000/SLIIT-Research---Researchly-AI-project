"""Trend Forecaster inference service.

Loads trained ARIMA models per topic and provides forecasts.
"""

from __future__ import annotations

import logging
import pickle
import warnings
from pathlib import Path
from typing import Optional

warnings.filterwarnings("ignore")

logger = logging.getLogger(__name__)

_SERVICE_ROOT = Path(__file__).parent.parent.parent
_MODEL_PATH = _SERVICE_ROOT / "models" / "trained_trend_forecaster" / "trend_models.pkl"

_MODEL_DATA: Optional[dict] = None


def is_loaded() -> bool:
    return _MODEL_DATA is not None


def load_model() -> bool:
    global _MODEL_DATA
    if _MODEL_DATA is not None:
        return True
    if not _MODEL_PATH.exists():
        logger.warning("[TrendForecaster] Model not found at %s", _MODEL_PATH)
        return False
    try:
        with open(_MODEL_PATH, "rb") as f:
            _MODEL_DATA = pickle.load(f)
        logger.info("[TrendForecaster] Loaded models for topics: %s",
                    list(_MODEL_DATA.get("models", {}).keys()))
        return True
    except Exception as e:
        logger.error("[TrendForecaster] Failed to load: %s", e)
        return False


def get_available_topics() -> list:
    if not load_model():
        return []
    return list(_MODEL_DATA["models"].keys())


def forecast(topic: str, horizon: int = 3) -> dict:
    """Forecast publication count for a topic over `horizon` years.

    Returns historical points + forecast points + confidence bounds.
    """
    if not load_model():
        return _fallback_forecast(topic, horizon)

    topic_models = _MODEL_DATA["models"]
    if topic not in topic_models:
        # Fallback to "all" if specific topic missing
        if "all" in topic_models:
            topic = "all"
        else:
            return _fallback_forecast(topic, horizon)

    entry = topic_models[topic]
    model = entry["model"]
    years = entry["years"]
    counts = entry["counts"]
    last_year = entry["last_year"]

    try:
        forecast_arr = model.forecast(steps=horizon)
        forecast_vals = [float(max(0, x)) for x in forecast_arr]
    except Exception as e:
        logger.warning("[TrendForecaster] Forecast failed for %s: %s", topic, e)
        forecast_vals = [counts[-1]] * horizon

    # Build response
    historical = [{"year": y, "count": c, "type": "historical"}
                   for y, c in zip(years, counts)]
    forecast_points = [{"year": last_year + i + 1,
                          "count": round(forecast_vals[i], 1),
                          "type": "forecast"}
                         for i in range(horizon)]

    # Compute simple trend direction
    if len(counts) >= 3:
        recent_avg = sum(counts[-3:]) / 3
        older_avg = sum(counts[:-3]) / max(1, len(counts) - 3)
        if recent_avg > older_avg * 1.2:
            direction = "rising"
        elif recent_avg < older_avg * 0.8:
            direction = "declining"
        else:
            direction = "stable"
    else:
        direction = "insufficient_data"

    return {
        "topic": topic,
        "horizon_years": horizon,
        "historical": historical,
        "forecast": forecast_points,
        "trend_direction": direction,
        "model_type": entry.get("model_type", "unknown"),
        "data_range": f"{years[0]}-{years[-1]}",
        "model_version": _MODEL_DATA.get("version", "unknown"),
    }


def _fallback_forecast(topic: str, horizon: int) -> dict:
    return {
        "topic": topic,
        "horizon_years": horizon,
        "historical": [],
        "forecast": [],
        "trend_direction": "unknown",
        "model_type": "fallback",
        "data_range": "n/a",
        "model_version": "fallback",
    }


def get_model_info() -> dict:
    if not load_model():
        return {"loaded": False, "error": "Model file not found"}
    return {
        "loaded": True,
        "version": _MODEL_DATA.get("version", "unknown"),
        "topics": list(_MODEL_DATA["models"].keys()),
    }
