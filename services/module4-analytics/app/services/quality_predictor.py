"""Quality Score Predictor inference service.

Loads trained XGBoost models and predicts quality dimensions for any paper text.
"""

from __future__ import annotations

import logging
import pickle
import re
from pathlib import Path
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

# Model path
_SERVICE_ROOT = Path(__file__).parent.parent.parent
_MODEL_PATH = _SERVICE_ROOT / "models" / "trained_quality_predictor" / "quality_models.pkl"

_MODEL_DATA: Optional[dict] = None


METHODOLOGY_KEYWORDS = [
    "experiment", "survey", "case study", "simulation", "prototype",
    "evaluation", "benchmark", "dataset", "statistical", "hypothesis",
    "mixed method", "qualitative", "quantitative", "systematic review",
    "regression", "interview", "questionnaire", "thematic analysis",
    "structural equation", "factor analysis", "anova", "correlation",
    "machine learning", "deep learning", "model", "algorithm",
]


def is_loaded() -> bool:
    return _MODEL_DATA is not None


def load_model() -> bool:
    """Load trained model from disk. Returns True on success."""
    global _MODEL_DATA
    if _MODEL_DATA is not None:
        return True
    if not _MODEL_PATH.exists():
        logger.warning("[QualityPredictor] Model not found at %s", _MODEL_PATH)
        return False
    try:
        with open(_MODEL_PATH, "rb") as f:
            _MODEL_DATA = pickle.load(f)
        logger.info("[QualityPredictor] Loaded models for targets: %s",
                    _MODEL_DATA.get("target_columns"))
        return True
    except Exception as e:
        logger.error("[QualityPredictor] Failed to load: %s", e)
        return False


def extract_features(title: str, abstract: str, authors: Optional[list] = None,
                      year: Optional[int] = None) -> dict:
    """Extract numerical features from paper text (matches training pipeline)."""
    title = title or ""
    abstract = abstract or ""
    authors = authors or []
    text = f"{title}\n\n{abstract}"

    words = text.split()
    word_count = len(words)
    sentences = max(1, text.count(".") + text.count("!") + text.count("?"))
    avg_word_len = sum(len(w) for w in words) / max(1, word_count)
    avg_sent_len = word_count / sentences

    text_lower = text.lower()
    method_hits = sum(1 for kw in METHODOLOGY_KEYWORDS if kw in text_lower)

    citation_brackets = len(re.findall(r"\[\d+\]", abstract))
    citation_parens = len(re.findall(r"\(\w+,?\s*\d{4}\)", abstract))
    citation_etal = len(re.findall(r"et\s+al\.?", abstract, re.IGNORECASE))
    total_citations = citation_brackets + citation_parens + citation_etal

    try:
        year_int = int(year) if year else 2024
    except (ValueError, TypeError):
        year_int = 2024

    return {
        "word_count": word_count,
        "title_word_count": len(title.split()),
        "sentence_count": sentences,
        "avg_word_length": round(avg_word_len, 2),
        "avg_sentence_length": round(avg_sent_len, 2),
        "methodology_keywords_count": method_hits,
        "author_count": len(authors),
        "citation_signals": total_citations,
        "year": year_int,
        "abstract_length": len(abstract),
        "title_length": len(title),
    }


def predict_quality(title: str, abstract: str, authors: Optional[list] = None,
                     year: Optional[int] = None) -> dict:
    """Predict quality scores for a paper.

    Returns dict with: overall, originality, citation_impact, methodology, clarity,
    plus features used and recommendations.
    """
    if not load_model():
        return _fallback_quality(title, abstract)

    features = extract_features(title, abstract, authors, year)
    feature_cols = _MODEL_DATA["feature_columns"]
    target_cols = _MODEL_DATA["target_columns"]
    models = _MODEL_DATA["models"]

    X = np.array([[features[c] for c in feature_cols]])
    scores = {}
    for tgt in target_cols:
        pred = float(models[tgt].predict(X)[0])
        # Clamp to [0, 1]
        scores[tgt] = round(max(0.0, min(1.0, pred)), 4)

    # Generate recommendations based on weak dimensions
    recommendations = []
    if scores["originality"] < 0.5:
        recommendations.append("Expand the abstract with more original analysis (current is short)")
    if scores["citation_impact"] < 0.5:
        recommendations.append("Add more citations to support claims (e.g., [1], (Author, Year))")
    if scores["methodology"] < 0.5:
        recommendations.append("Describe methodology more clearly (e.g., experiment, survey, dataset)")
    if scores["clarity"] < 0.5:
        recommendations.append("Improve readability — sentences are too long or words too complex")

    return {
        "overall_score": scores["overall"],
        "originality_score": scores["originality"],
        "citation_impact_score": scores["citation_impact"],
        "methodology_score": scores["methodology"],
        "clarity_score": scores["clarity"],
        "features": features,
        "recommendations": recommendations,
        "model_version": _MODEL_DATA.get("version", "unknown"),
    }


def _fallback_quality(title: str, abstract: str) -> dict:
    """Used when trained model is unavailable."""
    return {
        "overall_score": 0.5,
        "originality_score": 0.5,
        "citation_impact_score": 0.5,
        "methodology_score": 0.5,
        "clarity_score": 0.5,
        "features": extract_features(title, abstract),
        "recommendations": ["Trained quality model not loaded - using default scores"],
        "model_version": "fallback",
    }


def get_model_info() -> dict:
    """Return model metadata for health endpoint."""
    if not load_model():
        return {"loaded": False, "error": "Model file not found"}
    return {
        "loaded": True,
        "version": _MODEL_DATA.get("version", "unknown"),
        "targets": _MODEL_DATA.get("target_columns", []),
        "metrics": _MODEL_DATA.get("metrics", {}),
    }
