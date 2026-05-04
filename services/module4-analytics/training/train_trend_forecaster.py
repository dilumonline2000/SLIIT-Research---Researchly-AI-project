"""
Train Trend Forecaster — Prophet/ARIMA on SLIIT publication time series.

Builds one model per topic, saves to models/trained_trend_forecaster/.
Uses ARIMA as primary (Prophet has Windows install issues).
"""

import json
import pickle
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.holtwinters import ExponentialSmoothing

warnings.filterwarnings("ignore")

# Paths
_SERVICE_ROOT = Path(__file__).parent.parent
_DATA_DIR = _SERVICE_ROOT / "data"
_MODELS_DIR = _SERVICE_ROOT / "models"
_MODELS_DIR.mkdir(exist_ok=True)

OUT_MODEL_DIR = _MODELS_DIR / "trained_trend_forecaster"
OUT_MODEL_DIR.mkdir(exist_ok=True)


def fit_arima(series: list, order=(1, 1, 1)):
    """Fit ARIMA model. Returns (model, forecast_func)."""
    if len(series) < 4:
        return None
    try:
        model = ARIMA(series, order=order)
        fitted = model.fit()
        return fitted
    except Exception:
        # Fall back to simpler order
        try:
            model = ARIMA(series, order=(0, 1, 0))
            fitted = model.fit()
            return fitted
        except Exception:
            return None


def fit_holtwinters(series: list):
    """Fallback exponential smoothing."""
    if len(series) < 4:
        return None
    try:
        model = ExponentialSmoothing(series, trend="add", seasonal=None)
        fitted = model.fit()
        return fitted
    except Exception:
        return None


def main():
    print("=" * 70)
    print("  TRAINING TREND FORECASTER (ARIMA per topic)")
    print("=" * 70 + "\n")

    trend_path = _DATA_DIR / "trend_data.json"
    if not trend_path.exists():
        print(f"[!] Trend data not found at {trend_path}")
        return

    with open(trend_path, "r", encoding="utf-8") as f:
        trend_data = json.load(f)

    print(f"[+] Loaded trend data for {len(trend_data)} topics\n")

    trained_models = {}
    metrics = {}

    for topic, points in trend_data.items():
        if not points:
            continue
        years = [p["year"] for p in points]
        counts = [p["count"] for p in points]

        if len(counts) < 4:
            print(f"   [{topic:18s}] SKIP (only {len(counts)} years)")
            continue

        # Try ARIMA first
        model = fit_arima(counts)
        model_type = "ARIMA(1,1,1)"
        if model is None:
            model = fit_holtwinters(counts)
            model_type = "ExpSmoothing"

        if model is None:
            print(f"   [{topic:18s}] FAILED to fit any model")
            continue

        # Forecast next 3 years
        try:
            forecast = model.forecast(steps=3)
            forecast_vals = [float(max(0, x)) for x in forecast]
        except Exception:
            forecast_vals = [counts[-1]] * 3

        # Compute simple in-sample fit RMSE
        try:
            fitted_vals = model.fittedvalues
            residuals = np.array(counts[-len(fitted_vals):]) - np.array(fitted_vals)
            rmse = float(np.sqrt(np.mean(residuals**2)))
        except Exception:
            rmse = 0.0

        trained_models[topic] = {
            "model": model,
            "model_type": model_type,
            "years": years,
            "counts": counts,
            "last_year": years[-1],
            "forecast_3y": forecast_vals,
        }
        metrics[topic] = {
            "model_type": model_type,
            "rmse": rmse,
            "data_points": len(counts),
            "year_range": f"{years[0]}-{years[-1]}",
        }
        print(f"   [{topic:18s}] {model_type:14s}  RMSE={rmse:6.2f}  "
              f"Forecast(+3y): {[round(v, 1) for v in forecast_vals]}")

    # Save models
    out_pkl = OUT_MODEL_DIR / "trend_models.pkl"
    with open(out_pkl, "wb") as f:
        pickle.dump({
            "models": trained_models,
            "metrics": metrics,
            "version": "sliit-v1-trend",
        }, f)
    print(f"\n[+] Saved {len(trained_models)} trend models -> {out_pkl}")

    # Save metadata
    meta_path = OUT_MODEL_DIR / "metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump({
            "model_type": "ARIMA / ExponentialSmoothing per topic",
            "version": "sliit-v1-trend",
            "topics": list(trained_models.keys()),
            "metrics": metrics,
        }, f, indent=2)
    print(f"[+] Saved metadata -> {meta_path}")

    print("\n" + "=" * 70)
    print("  TREND FORECASTER TRAINING COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
