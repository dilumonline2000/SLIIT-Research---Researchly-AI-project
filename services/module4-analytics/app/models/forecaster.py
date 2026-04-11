"""Model wrapper for ARIMA + Prophet Ensemble Forecaster — inference time."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

DEFAULT_MODEL_DIR = Path(__file__).parent.parent.parent / "models" / "forecasting"


class TrendForecasterModel:
    """Wrapper for the trained ARIMA + Prophet ensemble forecaster."""

    def __init__(self, model_dir: str | Path | None = None):
        self.model_dir = Path(model_dir) if model_dir else DEFAULT_MODEL_DIR
        self._models: dict[str, dict] = {}

    def load(self, topic: str | None = None) -> None:
        """Load trained models for a specific topic or all topics."""
        import joblib

        if topic:
            topics_to_load = [topic]
        else:
            topics_to_load = [
                d.name for d in self.model_dir.iterdir()
                if d.is_dir() and (d / "ensemble_weights.json").exists()
            ]

        for t in topics_to_load:
            topic_dir = self.model_dir / t
            if not topic_dir.exists():
                logger.warning("No model directory for topic: %s", t)
                continue

            entry: dict = {"arima": None, "prophet": None, "weights": {}}

            arima_path = topic_dir / "arima_model.pkl"
            if arima_path.exists():
                entry["arima"] = joblib.load(arima_path)

            prophet_path = topic_dir / "prophet_model.pkl"
            if prophet_path.exists():
                entry["prophet"] = joblib.load(prophet_path)

            weights_path = topic_dir / "ensemble_weights.json"
            if weights_path.exists():
                with open(weights_path) as f:
                    entry["weights"] = json.load(f)

            self._models[t] = entry
            logger.info("Loaded forecaster for topic: %s", t)

    def get_available_topics(self) -> list[str]:
        """List topics with trained models."""
        if not self._models:
            self.load()
        return list(self._models.keys())

    def forecast(self, topic: str, horizon_months: int = 12) -> dict:
        """Generate forecast for a topic.

        Returns: {dates: list[str], values: list[float], model_contributions: dict}
        """
        if topic not in self._models:
            self.load(topic)

        if topic not in self._models:
            return {"error": f"No model found for topic: {topic}"}

        entry = self._models[topic]
        weights = entry["weights"]
        forecasts = {}

        if entry["arima"] is not None and "arima" in weights:
            forecasts["arima"] = entry["arima"].predict(n_periods=horizon_months)

        if entry["prophet"] is not None and "prophet" in weights:
            future = entry["prophet"].make_future_dataframe(periods=horizon_months, freq="MS")
            prophet_forecast = entry["prophet"].predict(future)
            forecasts["prophet"] = prophet_forecast["yhat"].values[-horizon_months:]

        if not forecasts:
            return {"error": "No component models available"}

        # Weighted ensemble
        total_weight = sum(weights.get(k, 0) for k in forecasts)
        if total_weight == 0:
            total_weight = len(forecasts)
            norm_weights = {k: 1.0 / total_weight for k in forecasts}
        else:
            norm_weights = {k: weights.get(k, 0) / total_weight for k in forecasts}

        ensemble = sum(forecasts[k] * norm_weights[k] for k in forecasts)

        import pandas as pd
        last_date = pd.Timestamp.now().normalize()
        dates = pd.date_range(start=last_date, periods=horizon_months, freq="MS")

        return {
            "topic": topic,
            "dates": [d.strftime("%Y-%m-%d") for d in dates],
            "values": [round(float(v), 2) for v in ensemble],
            "weights": norm_weights,
        }
