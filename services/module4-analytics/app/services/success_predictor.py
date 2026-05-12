"""Success Predictor inference service.

Predicts probability that a research paper/proposal will be successful
(publishable, complete, high-quality).
"""

from __future__ import annotations

import logging
import pickle
from pathlib import Path
from typing import Optional

import numpy as np

from .quality_predictor import extract_features

logger = logging.getLogger(__name__)

_SERVICE_ROOT = Path(__file__).parent.parent.parent
_MODEL_PATH = _SERVICE_ROOT / "models" / "trained_success_predictor" / "success_model.pkl"

_MODEL_DATA: Optional[dict] = None


def is_loaded() -> bool:
    return _MODEL_DATA is not None


def load_model() -> bool:
    global _MODEL_DATA
    if _MODEL_DATA is not None:
        return True
    if not _MODEL_PATH.exists():
        logger.warning("[SuccessPredictor] Model not found at %s", _MODEL_PATH)
        return False
    try:
        with open(_MODEL_PATH, "rb") as f:
            _MODEL_DATA = pickle.load(f)
        logger.info("[SuccessPredictor] Model loaded (version: %s)",
                    _MODEL_DATA.get("version", "?"))
        return True
    except Exception as e:
        logger.error("[SuccessPredictor] Failed to load: %s", e)
        return False


def _heuristic_score(features: dict) -> float:
    """Fair quality-based success probability.

    The trained XGBoost model is a near-perfect memorisation of the training
    heuristic, but that heuristic is biased against technical papers:
      - it penalises avg_word_length > 6.5 (all CS/security papers exceed this)
      - it requires inline citations in the abstract ("[1]" / "et al.")

    This function applies the same structure but with thresholds calibrated for
    technical/domain papers, and is blended with the model output in
    predict_success() to prevent extreme 0% / 100% outputs.
    """
    abstract_length    = features["abstract_length"]
    method_count       = features["methodology_keywords_count"]
    citation_signals   = features["citation_signals"]
    avg_sent_len       = features["avg_sentence_length"]
    avg_word_len       = features["avg_word_length"]
    author_count       = features["author_count"]

    # Originality: adequate abstract length (min 300 chars to avoid short PDFs)
    originality = min(1.0, abstract_length / 1200.0)
    if abstract_length < 150:
        originality *= 0.5

    # Citation impact — give partial credit even without inline citations
    # (many fields put citations only in the body, not the abstract)
    if citation_signals > 0:
        citation_base = min(1.0, citation_signals / 3.0)
    else:
        citation_base = 0.25  # partial credit — absence of abstract citations ≠ no citations
    collaboration_bonus = 0.25 if author_count > 1 else 0.0
    citation_impact = min(1.0, citation_base + collaboration_bonus)

    # Methodology: 4-keyword threshold (not 6) — easier for specialised papers
    methodology = min(1.0, method_count / 4.0)

    # Clarity: penalise only above 7.5 avg word length (not 6.5).
    # CS / security / medical papers routinely exceed 6.5 by nature.
    clarity_penalty_word = max(0.0, (avg_word_len - 7.5) / 4.0)
    clarity_penalty_sent = max(0.0, (avg_sent_len - 28) / 30.0)
    clarity = max(0.4, min(1.0, 1.0 - clarity_penalty_word - clarity_penalty_sent))

    overall = (
        originality    * 0.30
        + citation_impact * 0.25
        + methodology  * 0.25
        + clarity      * 0.20
    )
    return round(min(1.0, overall), 4)


def predict_success(title: str, abstract: str, authors: Optional[list] = None,
                     year: Optional[int] = None) -> dict:
    """Predict success probability for a paper.

    Returns:
        {
            "success_probability": float (0-1),
            "prediction": "successful" | "needs_improvement",
            "confidence": float,
            "risk_level": "low" | "medium" | "high",
            "recommendations": list[str],
            "features": dict,
        }
    """
    features = extract_features(title, abstract, authors, year)

    # Compute fair heuristic score first — used as a safety net so the model
    # cannot produce extreme 0% / 100% outputs for legitimate technical papers.
    heuristic = _heuristic_score(features)

    if load_model():
        feature_cols = _MODEL_DATA["feature_columns"]
        model = _MODEL_DATA["model"]
        X = np.array([[features[c] for c in feature_cols]])
        model_proba = float(model.predict_proba(X)[0][1])
        # Blend: heuristic dominates (60 %) so technical papers are not unfairly
        # penalised by the model's over-fitted narrow training distribution.
        proba = round(0.40 * model_proba + 0.60 * heuristic, 4)
        version = _MODEL_DATA.get("version", "unknown")
    else:
        logger.warning("[SuccessPredictor] Model not loaded — using heuristic only")
        proba = heuristic
        version = "heuristic-only"

    prediction = "successful" if proba >= 0.5 else "needs_improvement"
    confidence = round(max(proba, 1 - proba), 4)

    if proba >= 0.7:
        risk_level = "low"
    elif proba >= 0.4:
        risk_level = "medium"
    else:
        risk_level = "high"

    # Generate actionable recommendations
    recommendations = []
    if features["methodology_keywords_count"] < 3:
        recommendations.append(
            "Strengthen methodology section — describe methods explicitly "
            "(e.g., experiment, survey, statistical analysis, dataset)"
        )
    if features["citation_signals"] < 2:
        recommendations.append(
            "Include citations or references in the abstract to support key claims"
        )
    if features["abstract_length"] < 500:
        recommendations.append(
            "Expand abstract to at least 500 characters with clear problem statement "
            "and contributions"
        )
    if features["author_count"] < 2:
        recommendations.append(
            "Consider collaboration — multi-author papers tend to perform better"
        )
    if features["avg_sentence_length"] > 30:
        recommendations.append(
            "Shorten sentences — average sentence length is high, hurts readability"
        )

    if not recommendations:
        recommendations.append("Strong paper across all dimensions — ready for submission")

    return {
        "success_probability": proba,
        "prediction": prediction,
        "confidence": confidence,
        "risk_level": risk_level,
        "recommendations": recommendations,
        "features": features,
        "model_version": version,
    }


def _fallback_predict(title: str, abstract: str) -> dict:
    features = extract_features(title, abstract)
    proba = _heuristic_score(features)
    return {
        "success_probability": proba,
        "prediction": "successful" if proba >= 0.5 else "needs_improvement",
        "confidence": round(max(proba, 1 - proba), 4),
        "risk_level": "low" if proba >= 0.7 else ("medium" if proba >= 0.4 else "high"),
        "recommendations": ["Trained model unavailable — using quality heuristic"],
        "features": features,
        "model_version": "heuristic-fallback",
    }


def get_model_info() -> dict:
    if not load_model():
        return {"loaded": False, "error": "Model file not found"}
    return {
        "loaded": True,
        "version": _MODEL_DATA.get("version", "unknown"),
        "metrics": _MODEL_DATA.get("metrics", {}),
    }
