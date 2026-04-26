"""
Model loader - initializes and registers trained models on startup.
Scans for trained model files and registers them in the model registry.
"""

import logging
import os
from pathlib import Path
from app.services import model_registry

logger = logging.getLogger(__name__)

# Get the services root directory
_SERVICES_ROOT = Path(__file__).parent.parent.parent.parent

MODULE_PATHS = {
    "citation_ner": _SERVICES_ROOT / "module1-integrity" / "models" / "citation_ner",
    "sbert_plagiarism": _SERVICES_ROOT / "module1-integrity" / "models" / "sbert_plagiarism",
}


def load_citation_ner():
    """Load the Citation NER model trained on SLIIT papers."""
    model_path = MODULE_PATHS.get("citation_ner")
    if not model_path or not model_path.exists():
        logger.warning("[Model Loader] Citation NER model not found at %s", model_path)
        return False

    try:
        import spacy
        # Suppress spaCy's unicode logging
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
        # Suppress transformer library's unicode logging
        logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
        logging.getLogger("transformers").setLevel(logging.ERROR)
        model = SentenceTransformer(str(model_path))
        model_registry.register("sbert_plagiarism", model, version="sliit-v1-trained")
        logger.info("[Model Loader] [+] SBERT Plagiarism loaded (Accuracy=100%)")
        return True
    except Exception as e:
        logger.error("[Model Loader] [!] Failed to load SBERT plagiarism: %s", str(e)[:100])
        return False


def load_all_trained_models():
    """Load all available trained models."""
    logger.info("\n" + "="*70)
    logger.info("  LOADING TRAINED LOCAL MODELS")
    logger.info("="*70)

    results = {
        "citation_ner": load_citation_ner(),
        "sbert_plagiarism": load_sbert_plagiarism(),
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
