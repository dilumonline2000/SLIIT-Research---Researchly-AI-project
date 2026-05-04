"""Topic Classifier inference service.

Loads trained SBERT encoder + LogisticRegression head and classifies
paper text into one of 6 topics.
"""

from __future__ import annotations

import logging
import pickle
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Suppress noisy logs
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)

_SERVICE_ROOT = Path(__file__).parent.parent.parent
_MODEL_PATH = _SERVICE_ROOT / "models" / "trained_topic_classifier" / "classifier.pkl"

_CLASSIFIER_DATA: Optional[dict] = None
_ENCODER = None


def is_loaded() -> bool:
    return _CLASSIFIER_DATA is not None and _ENCODER is not None


def load_model() -> bool:
    """Load trained classifier and encoder. Returns True on success."""
    global _CLASSIFIER_DATA, _ENCODER
    if is_loaded():
        return True
    if not _MODEL_PATH.exists():
        logger.warning("[TopicClassifier] Model not found at %s", _MODEL_PATH)
        return False
    try:
        with open(_MODEL_PATH, "rb") as f:
            _CLASSIFIER_DATA = pickle.load(f)

        from sentence_transformers import SentenceTransformer
        encoder_name = _CLASSIFIER_DATA.get("encoder_name", "sentence-transformers/all-MiniLM-L6-v2")
        _ENCODER = SentenceTransformer(encoder_name)
        logger.info("[TopicClassifier] Loaded classifier with labels: %s",
                    _CLASSIFIER_DATA.get("labels"))
        return True
    except Exception as e:
        logger.error("[TopicClassifier] Failed to load: %s", e)
        return False


def classify(text: str, top_k: int = 3) -> dict:
    """Classify text into topics. Returns top-k predictions with confidence."""
    if not load_model():
        return _fallback_classify()

    embedding = _ENCODER.encode([text], convert_to_numpy=True, show_progress_bar=False)
    clf = _CLASSIFIER_DATA["classifier"]
    proba = clf.predict_proba(embedding)[0]
    labels = clf.classes_

    # Sort by probability
    pairs = sorted(zip(labels, proba), key=lambda x: -x[1])
    top_predictions = [
        {"label": str(label), "confidence": round(float(p), 4)}
        for label, p in pairs[:top_k]
    ]

    return {
        "primary_topic": top_predictions[0]["label"],
        "confidence": top_predictions[0]["confidence"],
        "top_predictions": top_predictions,
        "model_version": _CLASSIFIER_DATA.get("version", "unknown"),
    }


def _fallback_classify() -> dict:
    return {
        "primary_topic": "general",
        "confidence": 0.0,
        "top_predictions": [{"label": "general", "confidence": 0.0}],
        "model_version": "fallback",
    }


def get_model_info() -> dict:
    if not load_model():
        return {"loaded": False, "error": "Model file not found"}
    clf = _CLASSIFIER_DATA["classifier"]
    return {
        "loaded": True,
        "version": _CLASSIFIER_DATA.get("version", "unknown"),
        "labels": list(clf.classes_),
        "encoder": _CLASSIFIER_DATA.get("encoder_name"),
    }
