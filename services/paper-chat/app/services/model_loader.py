"""
Model loader - initializes and registers trained models on startup.
Scans for trained model files and registers them in the model registry.
"""

import logging
import pickle
from pathlib import Path
from app.services import model_registry

logger = logging.getLogger(__name__)

# Get the services root directory
_SERVICES_ROOT = Path(__file__).parent.parent.parent.parent

MODULE_PATHS = {
    "citation_ner": _SERVICES_ROOT / "module1-integrity" / "models" / "citation_ner",
    "sbert_plagiarism": _SERVICES_ROOT / "module1-integrity" / "models" / "sbert_plagiarism",
    "supervisor_matcher": _SERVICES_ROOT / "module2-collaboration" / "models" / "trained_supervisor_matcher",
    "quality_scorer": _SERVICES_ROOT / "module4-analytics" / "models" / "trained_quality_predictor" / "quality_models.pkl",
    "topic_classifier": _SERVICES_ROOT / "module4-analytics" / "models" / "trained_topic_classifier" / "classifier.pkl",
    "trend_forecaster": _SERVICES_ROOT / "module4-analytics" / "models" / "trained_trend_forecaster" / "trend_models.pkl",
}


def load_citation_ner():
    """Load the Citation NER model trained on SLIIT papers."""
    model_path = MODULE_PATHS.get("citation_ner")
    if not model_path or not model_path.exists():
        logger.warning("[Model Loader] Citation NER model not found at %s", model_path)
        return False

    try:
        import spacy
        logging.getLogger("spacy").setLevel(logging.ERROR)
        model = spacy.load(str(model_path))
        model_registry.register("citation_ner", model, version="sliit-v1-trained")
        logger.info("[Model Loader] [+] Citation NER loaded (F1=99.45%)")
        return True
    except Exception as e:
        logger.error("[Model Loader] [!] Failed to load Citation NER: %s", str(e)[:100])
        return False


def load_sbert_plagiarism():
    """Load the SBERT model fine-tuned for plagiarism detection."""
    model_path = MODULE_PATHS.get("sbert_plagiarism")
    if not model_path or not model_path.exists():
        logger.warning("[Model Loader] SBERT plagiarism model not found at %s", model_path)
        return False

    try:
        from sentence_transformers import SentenceTransformer
        logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
        logging.getLogger("transformers").setLevel(logging.ERROR)
        model = SentenceTransformer(str(model_path))
        model_registry.register("sbert_plagiarism", model, version="sliit-v1-trained")
        logger.info("[Model Loader] [+] SBERT Plagiarism loaded (Accuracy=100%)")
        return True
    except Exception as e:
        logger.error("[Model Loader] [!] Failed to load SBERT plagiarism: %s", str(e)[:100])
        return False


def load_supervisor_matcher():
    """Load the supervisor matcher SBERT model (Module 2)."""
    model_path = MODULE_PATHS.get("supervisor_matcher")
    if not model_path or not model_path.exists():
        logger.warning("[Model Loader] Supervisor matcher not found at %s", model_path)
        return False
    try:
        from sentence_transformers import SentenceTransformer
        logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
        logging.getLogger("transformers").setLevel(logging.ERROR)
        model = SentenceTransformer(str(model_path))
        model_registry.register("supervisor_matcher", model, version="sliit-v1-trained")
        logger.info("[Model Loader] [+] Supervisor Matcher loaded")
        return True
    except Exception as e:
        logger.error("[Model Loader] [!] Failed to load Supervisor Matcher: %s", str(e)[:100])
        return False


def _load_pickle_model(name: str, log_label: str) -> bool:
    """Generic loader for pickle-based models (XGBoost, SBERT classifier, ARIMA)."""
    model_path = MODULE_PATHS.get(name)
    if not model_path or not model_path.exists():
        logger.warning("[Model Loader] %s not found at %s", log_label, model_path)
        return False
    try:
        with open(model_path, "rb") as f:
            data = pickle.load(f)
        version = data.get("version", "sliit-v1-trained") if isinstance(data, dict) else "sliit-v1-trained"
        model_registry.register(name, data, version=version)
        logger.info("[Model Loader] [+] %s loaded", log_label)
        return True
    except Exception as e:
        logger.error("[Model Loader] [!] Failed to load %s: %s", log_label, str(e)[:100])
        return False


def load_quality_scorer():
    return _load_pickle_model("quality_scorer", "Quality Scorer (Module 4)")


def load_topic_classifier():
    return _load_pickle_model("topic_classifier", "Topic Classifier (Module 4)")


def load_trend_forecaster():
    return _load_pickle_model("trend_forecaster", "Trend Forecaster (Module 4)")


def load_all_trained_models():
    """Load all available trained models."""
    logger.info("\n" + "="*70)
    logger.info("  LOADING TRAINED LOCAL MODELS")
    logger.info("="*70)

    results = {
        "citation_ner": load_citation_ner(),
        "sbert_plagiarism": load_sbert_plagiarism(),
        "supervisor_matcher": load_supervisor_matcher(),
        "quality_scorer": load_quality_scorer(),
        "topic_classifier": load_topic_classifier(),
        "trend_forecaster": load_trend_forecaster(),
    }

    loaded_count = sum(1 for v in results.values() if v)
    total_count = len(results)

    logger.info("")
    logger.info("[Model Loader] Summary: %d/%d models loaded", loaded_count, total_count)

    for name, loaded in results.items():
        status = "[+]" if loaded else "[!]"
        logger.info("  %s %s", status, name)

    logger.info("="*70 + "\n")

    return results


async def async_load_all_trained_models():
    """Async wrapper for model loading."""
    return load_all_trained_models()
