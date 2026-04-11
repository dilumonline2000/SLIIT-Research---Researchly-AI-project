"""Model 7: ARIMA + Prophet Ensemble — trend forecasting.

Architecture: Auto-ARIMA (SARIMA) + Prophet with academic seasonality
Ensemble: Weighted average (weights selected by validation MAPE)
Target: MAPE < 22%, directional accuracy > 75%

Usage:
    python ml/training/train_forecaster.py
    python ml/training/train_forecaster.py --horizon 12 --min-history 24
"""

from __future__ import annotations

import argparse
import json
import logging
import warnings
from pathlib import Path
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

try:
    import pmdarima as pm
    HAS_PMDARIMA = True
except ImportError:
    HAS_PMDARIMA = False

try:
    from prophet import Prophet
    HAS_PROPHET = True
except ImportError:
    HAS_PROPHET = False

from sklearn.metrics import mean_absolute_percentage_error

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)
warnings.filterwarnings("ignore")


def load_time_series(data_dir: str) -> dict[str, pd.DataFrame]:
    """Load topic frequency time series data.

    Returns dict mapping topic_name -> DataFrame with columns [ds, y].
    """
    ts_file = Path(data_dir) / "topic_timeseries.json"
    if ts_file.exists():
        with open(ts_file, "r", encoding="utf-8") as f:
            raw = json.load(f)
        series = {}
        for topic, records in raw.items():
            df = pd.DataFrame(records)
            df["ds"] = pd.to_datetime(df["ds"])
            df = df.sort_values("ds").reset_index(drop=True)
            series[topic] = df
        return series

    logger.warning("No time series data found, generating synthetic data")
    return _synthetic_time_series()


def _synthetic_time_series() -> dict[str, pd.DataFrame]:
    """Generate synthetic monthly publication counts for testing."""
    np.random.seed(42)
    topics = [
        "Machine Learning", "Natural Language Processing",
        "Computer Vision", "Cybersecurity", "IoT",
    ]
    series = {}
    for i, topic in enumerate(topics):
        dates = pd.date_range(start="2019-01-01", periods=60, freq="MS")
        # Trend + seasonality + noise
        trend = np.linspace(50 + i * 10, 120 + i * 15, 60)
        seasonal = 15 * np.sin(np.arange(60) * 2 * np.pi / 12)  # yearly
        academic = 10 * np.sin(np.arange(60) * 2 * np.pi / 6)  # semester
        noise = np.random.normal(0, 5, 60)
        values = np.maximum(trend + seasonal + academic + noise, 1).astype(int)
        series[topic] = pd.DataFrame({"ds": dates, "y": values})
    return series


def train_arima(train_df: pd.DataFrame) -> object | None:
    """Fit auto-ARIMA (SARIMA) model."""
    if not HAS_PMDARIMA:
        logger.warning("pmdarima not installed — skipping ARIMA")
        return None

    model = pm.auto_arima(
        train_df["y"].values,
        seasonal=True,
        m=12,  # monthly seasonality
        max_p=5, max_d=2, max_q=5,
        max_P=2, max_D=1, max_Q=2,
        stepwise=True,
        suppress_warnings=True,
        error_action="ignore",
    )
    return model


def train_prophet(train_df: pd.DataFrame) -> object | None:
    """Fit Prophet with academic semester seasonality."""
    if not HAS_PROPHET:
        logger.warning("prophet not installed — skipping Prophet")
        return None

    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=False,
        daily_seasonality=False,
        changepoint_prior_scale=0.05,
    )
    model.add_seasonality(
        name="academic_semester",
        period=182.5,
        fourier_order=3,
    )
    model.fit(train_df[["ds", "y"]])
    return model


def forecast_arima(model, horizon: int) -> np.ndarray:
    """Generate ARIMA forecasts."""
    return model.predict(n_periods=horizon)


def forecast_prophet(model, horizon: int) -> np.ndarray:
    """Generate Prophet forecasts."""
    future = model.make_future_dataframe(periods=horizon, freq="MS")
    forecast = model.predict(future)
    return forecast["yhat"].values[-horizon:]


def compute_metrics(actual: np.ndarray, predicted: np.ndarray) -> dict:
    """Compute MAPE and directional accuracy."""
    mape = mean_absolute_percentage_error(actual, predicted)
    # Directional accuracy: did we predict the direction of change correctly?
    actual_diff = np.diff(actual)
    pred_diff = np.diff(predicted)
    if len(actual_diff) > 0:
        dir_acc = np.mean(np.sign(actual_diff) == np.sign(pred_diff))
    else:
        dir_acc = 0.0
    return {"mape": float(mape), "directional_accuracy": float(dir_acc)}


def train_forecaster(
    output_dir: str = "services/module4-analytics/models/forecasting",
    data_dir: str = "ml/data/processed/performance",
    forecast_horizon: int = 12,
    min_history: int = 24,
    validation_window: int = 6,
) -> None:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    all_series = load_time_series(data_dir)
    logger.info("Loaded %d topic time series", len(all_series))

    results = {}

    for topic, df in all_series.items():
        if len(df) < min_history:
            logger.warning("Skipping %s: only %d data points (need %d)", topic, len(df), min_history)
            continue

        logger.info("Training forecasters for: %s (%d data points)", topic, len(df))

        # Split: hold out last validation_window months
        train_df = df.iloc[:-validation_window]
        val_df = df.iloc[-validation_window:]
        actual = val_df["y"].values

        # Train both models
        arima_model = train_arima(train_df)
        prophet_model = train_prophet(train_df)

        # Generate validation forecasts
        forecasts = {}
        weights = {}

        if arima_model is not None:
            arima_pred = forecast_arima(arima_model, validation_window)
            arima_metrics = compute_metrics(actual, arima_pred)
            forecasts["arima"] = arima_pred
            weights["arima"] = 1.0 / max(arima_metrics["mape"], 0.01)
            logger.info("  ARIMA — MAPE: %.4f, DirAcc: %.4f", arima_metrics["mape"], arima_metrics["directional_accuracy"])

        if prophet_model is not None:
            prophet_pred = forecast_prophet(prophet_model, validation_window)
            prophet_metrics = compute_metrics(actual, prophet_pred)
            forecasts["prophet"] = prophet_pred
            weights["prophet"] = 1.0 / max(prophet_metrics["mape"], 0.01)
            logger.info("  Prophet — MAPE: %.4f, DirAcc: %.4f", prophet_metrics["mape"], prophet_metrics["directional_accuracy"])

        if not forecasts:
            logger.warning("  No models trained for %s", topic)
            continue

        # Weighted ensemble
        total_weight = sum(weights.values())
        norm_weights = {k: v / total_weight for k, v in weights.items()}
        ensemble_pred = sum(forecasts[k] * norm_weights[k] for k in forecasts)
        ensemble_metrics = compute_metrics(actual, ensemble_pred)

        logger.info(
            "  Ensemble — MAPE: %.4f, DirAcc: %.4f, Weights: %s",
            ensemble_metrics["mape"], ensemble_metrics["directional_accuracy"],
            {k: f"{v:.3f}" for k, v in norm_weights.items()},
        )

        # Save models for this topic
        topic_dir = output_path / topic.lower().replace(" ", "_")
        topic_dir.mkdir(parents=True, exist_ok=True)

        if arima_model is not None:
            import joblib
            joblib.dump(arima_model, topic_dir / "arima_model.pkl")

        if prophet_model is not None:
            import joblib
            joblib.dump(prophet_model, topic_dir / "prophet_model.pkl")

        # Save weights
        with open(topic_dir / "ensemble_weights.json", "w") as f:
            json.dump(norm_weights, f, indent=2)

        results[topic] = {
            "data_points": len(df),
            "ensemble_weights": norm_weights,
            "val_mape": ensemble_metrics["mape"],
            "val_directional_accuracy": ensemble_metrics["directional_accuracy"],
        }

    # Save overall metadata
    metadata = {
        "model": "trend-forecaster",
        "type": "arima-prophet-ensemble",
        "forecast_horizon_months": forecast_horizon,
        "validation_window_months": validation_window,
        "topics_trained": len(results),
        "results": results,
    }
    with open(output_path / "training_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    logger.info("Forecaster training complete for %d topics", len(results))


def main():
    parser = argparse.ArgumentParser(description="Train ARIMA + Prophet ensemble forecaster")
    parser.add_argument("--output", default="services/module4-analytics/models/forecasting")
    parser.add_argument("--data", default="ml/data/processed/performance")
    parser.add_argument("--horizon", type=int, default=12)
    parser.add_argument("--min-history", type=int, default=24)
    parser.add_argument("--val-window", type=int, default=6)
    args = parser.parse_args()
    train_forecaster(
        output_dir=args.output, data_dir=args.data,
        forecast_horizon=args.horizon, min_history=args.min_history,
        validation_window=args.val_window,
    )


if __name__ == "__main__":
    main()
