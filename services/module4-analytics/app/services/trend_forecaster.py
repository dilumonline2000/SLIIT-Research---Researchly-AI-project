"""Trend Forecaster inference service.

Loads trained ARIMA models per topic and exposes:

  • forecast(topic, horizon)      → historical + forecast points + confidence intervals
  • forecast_many(topics, horizon)→ multi-topic forecast (used by the comparison view)
  • emerging_topics()             → topics with the steepest recent growth
  • recommendations(horizon)      → "best area to focus" auto-suggestions
  • model_metrics(topic)          → RMSE / MAE on the in-sample fit
  • get_available_topics() / get_model_info()

The model bundle (`models/trained_trend_forecaster/trend_models.pkl`) was created
by `training/train_trend_forecaster.py`. Each entry has shape:
    {
      "model": <fitted statsmodels ARIMA results>,
      "years": [int...],          historical years
      "counts": [float...],       paper counts per year
      "last_year": int,
      "model_type": "ARIMA(p,d,q)",
    }
"""

from __future__ import annotations

import logging
import math
import pickle
import warnings
from pathlib import Path
from typing import Any, Optional

warnings.filterwarnings("ignore")

logger = logging.getLogger(__name__)

_SERVICE_ROOT = Path(__file__).parent.parent.parent
_MODEL_PATH = _SERVICE_ROOT / "models" / "trained_trend_forecaster" / "trend_models.pkl"

_MODEL_DATA: Optional[dict[str, Any]] = None
# Per-topic computed metrics (lazy)
_METRICS_CACHE: dict[str, dict[str, float]] = {}
# Last load error so /health can return an *actionable* diagnostic instead
# of a generic "Model file not found" when the real cause is an import error.
_LAST_LOAD_ERROR: str = ""


def is_loaded() -> bool:
    return _MODEL_DATA is not None


def load_model() -> bool:
    global _MODEL_DATA, _LAST_LOAD_ERROR
    if _MODEL_DATA is not None:
        return True
    if not _MODEL_PATH.exists():
        _LAST_LOAD_ERROR = f"Model file not found at {_MODEL_PATH}"
        logger.warning("[TrendForecaster] %s", _LAST_LOAD_ERROR)
        return False
    try:
        with open(_MODEL_PATH, "rb") as f:
            _MODEL_DATA = pickle.load(f)
        _LAST_LOAD_ERROR = ""
        logger.info("[TrendForecaster] Loaded models for topics: %s",
                    list(_MODEL_DATA.get("models", {}).keys()))
        return True
    except ModuleNotFoundError as e:
        _LAST_LOAD_ERROR = (
            f"Cannot unpickle model — missing Python package '{e.name}'. "
            f"Run: pip install {e.name} (and restart the service)."
        )
        logger.error("[TrendForecaster] %s", _LAST_LOAD_ERROR)
        return False
    except Exception as e:
        _LAST_LOAD_ERROR = f"Failed to load model: {type(e).__name__}: {e}"
        logger.error("[TrendForecaster] %s", _LAST_LOAD_ERROR)
        return False


def get_available_topics() -> list[str]:
    if not load_model():
        return []
    return list(_MODEL_DATA["models"].keys())


# ─── Per-topic forecast + CI ─────────────────────────────────────────────


def _forecast_with_ci(entry: dict[str, Any], horizon: int) -> tuple[list[float], list[float], list[float]]:
    """Return (mean, lower, upper) for the next `horizon` steps.

    Uses statsmodels' `get_forecast()` to extract the 95 % prediction interval.
    Falls back to a heuristic ±1.96·σ band when the model object lacks the API.
    """
    model = entry["model"]
    counts = entry.get("counts") or []

    # statsmodels ARIMAResults
    try:
        gf = model.get_forecast(steps=horizon)
        mean = [float(max(0, x)) for x in gf.predicted_mean]
        ci = gf.conf_int(alpha=0.05)
        # ci is a numpy array shape (horizon, 2) or pandas DataFrame
        try:
            lower = [float(max(0, ci.iloc[i, 0])) for i in range(horizon)]
            upper = [float(max(0, ci.iloc[i, 1])) for i in range(horizon)]
        except AttributeError:
            lower = [float(max(0, ci[i, 0])) for i in range(horizon)]
            upper = [float(max(0, ci[i, 1])) for i in range(horizon)]
        # Some ARIMA fits give pathologically wide bands when residual variance
        # is large. Cap at +200 % of the historical max.
        cap = max(counts) * 3 if counts else 100
        upper = [min(u, cap) for u in upper]
        return mean, lower, upper
    except Exception as e:
        logger.info("[TrendForecaster] get_forecast() unavailable (%s) — using heuristic CI", e)

    # Fallback: simple forecast + ±1.96·σ from the residuals
    try:
        forecast_arr = model.forecast(steps=horizon)
        mean = [float(max(0, x)) for x in forecast_arr]
    except Exception:
        mean = [counts[-1] if counts else 0.0] * horizon
    sigma = _residual_std(model, counts) if counts else 1.0
    half = 1.96 * sigma
    lower = [max(0.0, m - half) for m in mean]
    upper = [m + half for m in mean]
    return mean, lower, upper


def _residual_std(model: Any, counts: list[float]) -> float:
    """Best-effort residual std for the heuristic CI fallback."""
    try:
        resid = getattr(model, "resid", None)
        if resid is None:
            return float(max(1.0, math.sqrt(sum(c * c for c in counts) / max(1, len(counts)))) * 0.2)
        vals = [float(x) for x in (resid.values if hasattr(resid, "values") else resid)]
        n = max(1, len(vals))
        mean = sum(vals) / n
        var = sum((v - mean) ** 2 for v in vals) / n
        return float(math.sqrt(var))
    except Exception:
        return 1.0


def _trend_direction(counts: list[float]) -> str:
    if len(counts) < 3:
        return "insufficient_data"
    recent = sum(counts[-3:]) / 3
    earlier = sum(counts[:-3]) / max(1, len(counts) - 3)
    if recent > earlier * 1.2:
        return "rising"
    if recent < earlier * 0.8:
        return "declining"
    return "stable"


def _growth_pct(counts: list[float], forecast: list[float]) -> float:
    """Percent change from latest historical to end-of-forecast value."""
    if not counts or not forecast:
        return 0.0
    base = counts[-1] or 1.0
    end = forecast[-1]
    return round((end - base) / base * 100, 1)


def _accuracy(model: Any, counts: list[float]) -> dict[str, float]:
    """Compute RMSE / MAE on the in-sample fit. Cached per topic."""
    try:
        fitted = getattr(model, "fittedvalues", None)
        if fitted is None:
            return {"rmse": 0.0, "mae": 0.0, "available": False}
        actual = list(counts)
        pred = [float(x) for x in (fitted.values if hasattr(fitted, "values") else fitted)]
        # Align lengths — ARIMA(d>0) drops the first `d` observations
        n = min(len(actual), len(pred))
        if n == 0:
            return {"rmse": 0.0, "mae": 0.0, "available": False}
        a = actual[-n:]
        p = pred[-n:]
        rmse = math.sqrt(sum((x - y) ** 2 for x, y in zip(a, p)) / n)
        mae = sum(abs(x - y) for x, y in zip(a, p)) / n
        # Normalise rmse against the mean for a 0..1 quality indicator
        mean = sum(a) / n if n else 1.0
        nrmse = rmse / mean if mean else 1.0
        return {
            "rmse": round(rmse, 3),
            "mae": round(mae, 3),
            "nrmse": round(nrmse, 3),
            "n_observations": n,
            "available": True,
        }
    except Exception as e:
        logger.debug("[TrendForecaster] accuracy calc failed: %s", e)
        return {"rmse": 0.0, "mae": 0.0, "available": False}


def model_metrics(topic: str) -> dict[str, Any]:
    if topic in _METRICS_CACHE:
        return _METRICS_CACHE[topic]
    if not load_model():
        return {"available": False}
    entry = _MODEL_DATA["models"].get(topic)
    if not entry:
        return {"available": False}
    out = _accuracy(entry["model"], entry.get("counts") or [])
    _METRICS_CACHE[topic] = out
    return out


def forecast(topic: str, horizon: int = 3) -> dict[str, Any]:
    if not load_model():
        return _fallback_forecast(topic, horizon)
    topic_models = _MODEL_DATA["models"]
    if topic not in topic_models:
        if "all" in topic_models:
            topic = "all"
        else:
            return _fallback_forecast(topic, horizon)

    entry = topic_models[topic]
    years = entry["years"]
    counts = entry["counts"]
    last_year = entry["last_year"]

    mean, lower, upper = _forecast_with_ci(entry, horizon)

    historical = [{"year": y, "count": c, "type": "historical"} for y, c in zip(years, counts)]
    forecast_pts = [{
        "year": last_year + i + 1,
        "count": round(mean[i], 1),
        "lower": round(lower[i], 1),
        "upper": round(upper[i], 1),
        "type": "forecast",
    } for i in range(horizon)]

    direction = _trend_direction(counts)
    growth_pct = _growth_pct(counts, mean)
    metrics = model_metrics(topic)

    # Build a one-sentence interpretation
    interpretation = _interpretation(topic, direction, growth_pct, last_year, horizon, mean, counts)

    return {
        "topic": topic,
        "horizon_years": horizon,
        "historical": historical,
        "forecast": forecast_pts,
        "trend_direction": direction,
        "growth_pct": growth_pct,
        "interpretation": interpretation,
        "accuracy": metrics,
        "model_type": entry.get("model_type", "unknown"),
        "data_range": f"{years[0]}-{years[-1]}",
        "model_version": _MODEL_DATA.get("version", "unknown"),
        "stats": {
            "historical_total": int(sum(counts)),
            "historical_peak": {"year": int(years[counts.index(max(counts))]), "count": int(max(counts))} if counts else None,
            "current_count": int(counts[-1]) if counts else 0,
            "forecast_end": round(mean[-1], 1) if mean else 0,
        },
    }


def _interpretation(topic: str, direction: str, growth_pct: float, last_year: int, horizon: int,
                     mean: list[float], counts: list[float]) -> str:
    end_year = last_year + horizon
    if direction == "insufficient_data":
        return f"Not enough historical data on **{topic}** for a confident interpretation."
    if direction == "rising":
        return (
            f"Research on **{topic}** is on a rising trajectory. The forecast projects "
            f"a **{growth_pct:+.0f}%** change by **{end_year}**. This is an actively growing "
            f"area — building on the most recent contributions is a strong move."
        )
    if direction == "declining":
        return (
            f"Publications on **{topic}** have been **declining**. The model expects a "
            f"**{growth_pct:+.0f}%** change by {end_year}. Either the topic is saturated "
            f"or it has shifted to neighbouring areas — worth investigating why."
        )
    return (
        f"Activity on **{topic}** is **stable** ({growth_pct:+.0f}% projected by {end_year}). "
        f"There is room for incremental contributions; novelty will require differentiation."
    )


def forecast_many(topics: list[str], horizon: int = 3) -> list[dict[str, Any]]:
    return [forecast(t, horizon) for t in topics if t]


# ─── Emerging-topic detection ────────────────────────────────────────────


def emerging_topics(horizon: int = 3, top_k: int = 5) -> list[dict[str, Any]]:
    """Rank topics by *recent* slope vs *long-term* slope.

    A topic with a much steeper recent growth than its overall trajectory is
    'emerging'. Excludes the 'all' aggregate.
    """
    if not load_model():
        return []
    out: list[dict[str, Any]] = []
    for topic, entry in _MODEL_DATA["models"].items():
        if topic == "all":
            continue
        counts: list[float] = entry.get("counts") or []
        if len(counts) < 5:
            continue
        # Recent slope (last 4 years)
        recent_slope = _slope(counts[-4:])
        long_slope = _slope(counts)
        # Latest absolute count, normalised
        latest = counts[-1]
        # Emergence = recent_slope amplified by how much it exceeds the long-term slope
        emergence = recent_slope - long_slope
        # Relative growth ratio (latest vs older average)
        older_avg = sum(counts[:-3]) / max(1, len(counts) - 3) if len(counts) > 3 else 1.0
        ratio = latest / max(older_avg, 1.0)

        # Composite score; require positive recent slope and meaningful latest count
        if recent_slope <= 0 or latest < 2:
            continue
        score = emergence * 0.5 + ratio * 0.5
        # Run a small forecast to give the user the ramp
        f = forecast(topic, horizon)
        out.append({
            "topic": topic,
            "score": round(float(score), 3),
            "recent_slope": round(recent_slope, 3),
            "long_term_slope": round(long_slope, 3),
            "latest_count": int(latest),
            "growth_ratio": round(ratio, 2),
            "growth_pct": f.get("growth_pct", 0),
            "interpretation": (
                f"**{topic.title()}** has a recent slope of {recent_slope:+.1f} papers/year "
                f"vs a long-term {long_slope:+.1f}/year — accelerating sharply."
            ),
        })
    out.sort(key=lambda x: x["score"], reverse=True)
    return out[:top_k]


def _slope(series: list[float]) -> float:
    """Linear-regression slope (least squares) on a short sequence."""
    n = len(series)
    if n < 2:
        return 0.0
    xs = list(range(n))
    x_mean = sum(xs) / n
    y_mean = sum(series) / n
    num = sum((xs[i] - x_mean) * (series[i] - y_mean) for i in range(n))
    den = sum((x - x_mean) ** 2 for x in xs)
    return num / den if den else 0.0


# ─── Predictive recommendations ──────────────────────────────────────────


def recommendations(horizon: int = 3, top_k: int = 5) -> list[dict[str, Any]]:
    """Suggest research areas combining high projected growth with low current saturation.

    Score = growth_pct (normalised) − saturation_penalty (latest_count / max_count).
    """
    if not load_model():
        return []

    raw: list[dict[str, Any]] = []
    counts_max = 1.0
    for topic, entry in _MODEL_DATA["models"].items():
        if topic == "all":
            continue
        counts = entry.get("counts") or []
        if len(counts) < 4:
            continue
        counts_max = max(counts_max, max(counts))
        f = forecast(topic, horizon)
        raw.append({"topic": topic, "growth_pct": f["growth_pct"], "latest": counts[-1], "interpretation": f["interpretation"]})

    out: list[dict[str, Any]] = []
    for r in raw:
        growth_norm = max(-1.0, min(2.0, r["growth_pct"] / 100.0))
        saturation = r["latest"] / counts_max
        score = growth_norm - 0.4 * saturation
        out.append({
            "topic": r["topic"],
            "score": round(float(score), 3),
            "growth_pct": r["growth_pct"],
            "latest_count": int(r["latest"]),
            "saturation": round(saturation, 2),
            "rationale": (
                f"Projected growth of **{r['growth_pct']:+.0f}%** with current activity at "
                f"{r['latest']} papers/year — "
                + ("low competition" if saturation < 0.4 else
                   "moderate competition" if saturation < 0.7 else
                   "high competition")
                + "."
            ),
            "suggested_title": f"Investigating {r['topic']}: opportunities through {2026 + horizon}",
        })
    out.sort(key=lambda x: x["score"], reverse=True)
    return out[:top_k]


# ─── Helpers ─────────────────────────────────────────────────────────────


def _fallback_forecast(topic: str, horizon: int) -> dict[str, Any]:
    return {
        "topic": topic,
        "horizon_years": horizon,
        "historical": [],
        "forecast": [],
        "trend_direction": "unknown",
        "growth_pct": 0.0,
        "interpretation": "Model not loaded.",
        "accuracy": {"available": False},
        "model_type": "fallback",
        "data_range": "n/a",
        "model_version": "fallback",
        "stats": {},
    }


def get_model_info() -> dict[str, Any]:
    if not load_model():
        return {"loaded": False, "error": _LAST_LOAD_ERROR or "Unknown load failure"}
    return {
        "loaded": True,
        "version": _MODEL_DATA.get("version", "unknown"),
        "topics": list(_MODEL_DATA["models"].keys()),
    }


# ─── HTML report generator ───────────────────────────────────────────────


def generate_report_html(payload: dict[str, Any]) -> str:
    """Render a self-contained HTML report from the API payload."""
    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    def esc(s: Any) -> str:
        return (str(s) if s is not None else "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    forecasts = payload.get("forecasts", [])
    insights = payload.get("insights") or {}
    emerging = insights.get("emerging") or []
    recs = insights.get("recommendations") or []

    forecast_blocks = ""
    for f in forecasts:
        rows = "".join(
            f"<tr><td>{esc(p['year'])}</td><td>{esc(p.get('count'))}</td>"
            f"<td>{esc(p.get('lower', '-'))} – {esc(p.get('upper', '-'))}</td></tr>"
            for p in f.get("forecast", [])
        )
        acc = f.get("accuracy") or {}
        forecast_blocks += f"""
        <div class="block">
          <h3>{esc(f.get('topic', '').title())}
            <span class="dir dir-{esc(f.get('trend_direction',''))}">{esc(f.get('trend_direction',''))}</span>
            <span class="growth">{f.get('growth_pct', 0):+.0f}% by horizon</span>
          </h3>
          <p>{esc(f.get('interpretation', ''))}</p>
          {f'<p class="meta">Accuracy — RMSE {acc.get("rmse",0):.2f}, MAE {acc.get("mae",0):.2f}</p>' if acc.get('available') else ''}
          <table>
            <thead><tr><th>Year</th><th>Forecast</th><th>95% CI</th></tr></thead>
            <tbody>{rows}</tbody>
          </table>
        </div>
        """

    emerging_html = "".join(
        f"<li><strong>{esc(e['topic'].title())}</strong> — {esc(e['interpretation'])}</li>"
        for e in emerging
    )
    rec_html = "".join(
        f"""<div class="rec">
          <h4>{esc(r['suggested_title'])}</h4>
          <p>{esc(r['rationale'])}</p>
        </div>""" for r in recs
    )

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8" />
<title>Research Trend Report</title>
<style>
  body {{ font-family: Georgia, 'Times New Roman', serif; max-width: 880px; margin: 2rem auto; padding: 0 1.5rem; color: #1f2937; line-height: 1.55; }}
  h1, h2, h3, h4 {{ color: #312e81; }}
  h1 {{ border-bottom: 3px solid #6366f1; padding-bottom: .5rem; }}
  h2 {{ margin-top: 2rem; border-bottom: 1px solid #c7d2fe; padding-bottom: .25rem; }}
  .block {{ border: 1px solid #e5e7eb; border-radius: 6px; padding: .75rem 1rem; margin: .75rem 0; background: #f9fafb; }}
  .dir {{ display: inline-block; padding: 1px 8px; border-radius: 999px; font-size: .7rem; margin-left: .5rem; text-transform: capitalize; }}
  .dir-rising {{ background: #d1fae5; color: #047857; }}
  .dir-declining {{ background: #fee2e2; color: #991b1b; }}
  .dir-stable {{ background: #dbeafe; color: #1e3a8a; }}
  .dir-insufficient_data, .dir-unknown {{ background: #f3f4f6; color: #4b5563; }}
  .growth {{ font-size: .8rem; color: #6b7280; margin-left: .5rem; }}
  table {{ border-collapse: collapse; width: 100%; margin-top: .5rem; }}
  th, td {{ padding: .35rem .5rem; border-bottom: 1px solid #e5e7eb; text-align: left; font-size: .85rem; }}
  .meta {{ font-size: .75rem; color: #6b7280; }}
  .rec {{ background: #eef2ff; border-left: 3px solid #6366f1; padding: .5rem .75rem; margin: .5rem 0; }}
</style></head><body>
  <h1>Research Trend Forecasting Report</h1>
  <p style="color:#4b5563;font-size:.9rem;">Generated {now} · {len(forecasts)} domain forecast(s)</p>

  <h2>1 · Forecasts</h2>
  {forecast_blocks or '<p>No forecasts.</p>'}

  <h2>2 · Emerging Topics</h2>
  <ul>{emerging_html or '<li>None detected.</li>'}</ul>

  <h2>3 · Recommended Research Areas</h2>
  {rec_html or '<p>No recommendations.</p>'}

  <hr style="margin-top:3rem"/>
  <p style="font-size:.75rem;color:#9ca3af;">Researchly AI · Module 4 (Trend Forecasting)</p>
</body></html>"""
