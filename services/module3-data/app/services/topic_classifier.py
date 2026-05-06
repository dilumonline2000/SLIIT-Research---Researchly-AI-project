"""Topic classifier inference service.

Loads the trained TF-IDF + One-vs-Rest LogReg bundle and exposes:
    is_loaded() -> bool
    load() -> bool
    classify(text: str, threshold: float = 0.3, top_k: int = 5) -> dict
    get_model_info() -> dict
"""

from __future__ import annotations

import logging
import pickle
from pathlib import Path
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)

SERVICE_ROOT = Path(__file__).resolve().parent.parent.parent
BUNDLE_PATH = SERVICE_ROOT / "models" / "trained_topic_classifier" / "classifier.pkl"

_BUNDLE: Optional[dict[str, Any]] = None


def is_loaded() -> bool:
    return _BUNDLE is not None


def load() -> bool:
    global _BUNDLE
    if _BUNDLE is not None:
        return True
    if not BUNDLE_PATH.exists():
        logger.warning("[TopicClassifier] bundle not found at %s", BUNDLE_PATH)
        return False
    try:
        with open(BUNDLE_PATH, "rb") as f:
            _BUNDLE = pickle.load(f)
        logger.info(
            "[TopicClassifier] loaded v%s — %d labels",
            _BUNDLE.get("version"), len(_BUNDLE["labels"]),
        )
        return True
    except Exception as e:
        logger.error("[TopicClassifier] failed to load: %s", e)
        return False


def classify(text: str, threshold: float = 0.3, top_k: int = 5) -> dict[str, Any]:
    """Multi-label classify the given text.

    Returns:
        {
          "loaded": bool,
          "categories": list[str],          # categories with prob >= threshold
          "confidence_scores": dict[label] = prob,
          "top_categories": list[(label, prob)]  # top-K regardless of threshold
        }
    """
    if not load():
        return {"loaded": False, "categories": [], "confidence_scores": {}, "top_categories": []}
    assert _BUNDLE is not None

    vec = _BUNDLE["vectorizer"]
    clf = _BUNDLE["classifier"]
    labels: list[str] = _BUNDLE["labels"]

    X = vec.transform([text or ""])
    try:
        probs = clf.predict_proba(X)[0]  # shape (n_labels,)
    except AttributeError:
        # OvR with non-probabilistic estimator — use decision function
        scores = clf.decision_function(X)[0]
        probs = 1.0 / (1.0 + np.exp(-scores))

    order = np.argsort(-probs)
    top = [(labels[int(i)], float(probs[int(i)])) for i in order[:top_k]]

    categories = [(labels[int(i)], float(probs[int(i)])) for i in order if probs[int(i)] >= threshold]
    confidence_scores = {lab: round(p, 4) for lab, p in categories}

    return {
        "loaded": True,
        "categories": [lab for lab, _ in categories],
        "confidence_scores": confidence_scores,
        "top_categories": [{"label": lab, "confidence": round(p, 4)} for lab, p in top],
        "model_version": _BUNDLE.get("version", "unknown"),
    }


def get_model_info() -> dict[str, Any]:
    if not load():
        return {"loaded": False, "error": "Bundle not found — run train_topic_classifier.py"}
    assert _BUNDLE is not None
    return {
        "loaded": True,
        "version": _BUNDLE.get("version", "unknown"),
        "n_labels": len(_BUNDLE["labels"]),
        "labels": _BUNDLE["labels"],
    }
