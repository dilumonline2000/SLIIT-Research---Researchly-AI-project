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
    if not load_model():
        return _fallback_predict(title, abstract)

    features = extract_features(title, abstract, authors, year)
    feature_cols = _MODEL_DATA["feature_columns"]
    model = _MODEL_DATA["model"]

    X = np.array([[features[c] for c in feature_cols]])
    proba = float(model.predict_proba(X)[0][1])
    prediction = "successful" if proba >= 0.5 else "needs_improvement"
    confidence = max(proba, 1 - proba)

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
    if features["citation_signals"] < 3:
        recommendations.append(
            "Add more citations and references to support claims"
        )
    if features["abstract_length"] < 800:
        recommendations.append(
            "Expand abstract to at least 800 characters with clear contributions"
        )
    if features["author_count"] < 2:
        recommendations.append(
            "Consider collaboration — multi-author papers tend to perform better"
        )
    if features["avg_sentence_length"] > 25:
        recommendations.append(
            "Shorten sentences — average is too long, hurts readability"
        )
    if features["avg_word_length"] > 6.5:
        recommendations.append(
            "Simplify vocabulary — avg word length is high, may be hard to read"
        )

    if not recommendations:
        recommendations.append("Strong paper across all dimensions — ready for submission")

    return {
        "success_probability": round(proba, 4),
        "prediction": prediction,
        "confidence": round(confidence, 4),
        "risk_level": risk_level,
        "recommendations": recommendations,
        "features": features,
        "model_version": _MODEL_DATA.get("version", "unknown"),
    }


def _fallback_predict(title: str, abstract: str) -> dict:
    return {
        "success_probability": 0.5,
        "prediction": "unknown",
        "confidence": 0.0,
        "risk_level": "unknown",
        "recommendations": ["Trained success predictor not loaded - using fallback"],
        "features": extract_features(title, abstract),
        "model_version": "fallback",
    }


def get_model_info() -> dict:
    if not load_model():
        return {"loaded": False, "error": "Model file not found"}
    return {
        "loaded": True,
        "version": _MODEL_DATA.get("version", "unknown"),
        "metrics": _MODEL_DATA.get("metrics", {}),
    }
