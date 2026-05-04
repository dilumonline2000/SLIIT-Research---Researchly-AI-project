"""Auto-loads all Module 4 trained models on service startup."""

import logging

from . import quality_predictor, topic_classifier, trend_forecaster, success_predictor

logger = logging.getLogger(__name__)


def load_all_models() -> dict:
    """Load all trained models. Returns {model_name: success_bool}."""
    results = {
        "quality_predictor": quality_predictor.load_model(),
        "topic_classifier": topic_classifier.load_model(),
        "trend_forecaster": trend_forecaster.load_model(),
        "success_predictor": success_predictor.load_model(),
    }

    for name, ok in results.items():
        prefix = "[+]" if ok else "[!]"
        logger.info("[Module4 Model Loader] %s %s", prefix, name)

    loaded_count = sum(1 for v in results.values() if v)
    logger.info("[Module4 Model Loader] %d/%d models loaded", loaded_count, len(results))
    return results


def get_status() -> dict:
    """Return current status of all models."""
    return {
        "quality_predictor": quality_predictor.get_model_info(),
        "topic_classifier": topic_classifier.get_model_info(),
        "trend_forecaster": trend_forecaster.get_model_info(),
        "success_predictor": success_predictor.get_model_info(),
    }
