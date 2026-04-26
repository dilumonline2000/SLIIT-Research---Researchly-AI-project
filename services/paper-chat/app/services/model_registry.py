"""
Central registry for all locally trained models.
Models register here after loading. Frontend queries this
to know if Local AI mode is available.
"""
from typing import Any, Dict

_registry: Dict[str, Any] = {}
_versions: Dict[str, str] = {}

MODEL_DESCRIPTIONS: Dict[str, str] = {
    "sbert": "Sentence-BERT embeddings for semantic search",
    "sbert_plagiarism": "SBERT fine-tuned for plagiarism detection (Module 1) [TRAINED]",
    "scibert_classifier": "SciBERT multi-label topic classifier",
    "rag_engine": "Retrieval-Augmented Generation over paper corpus",
    "citation_ner": "spaCy NER for citation entity extraction (Module 1) [TRAINED]",
    "summarizer": "BART/T5 abstractive summarizer",
    "sentiment_bert": "BERT aspect-based sentiment for feedback",
    "trend_forecaster": "ARIMA + Prophet ensemble for trend prediction",
    "quality_scorer": "Multi-dimensional research quality scorer",
    "success_predictor": "XGBoost/RF project success predictor",
    "proposal_llm": "LoRA fine-tuned LLM for proposal generation",
}

CORE_MODELS = {"sbert", "rag_engine"}
TRAINED_MODELS = {"citation_ner", "sbert_plagiarism"}  # Models we've trained


def register(name: str, model: Any, version: str = "v1.0") -> None:
    """Call this after a model finishes loading."""
    _registry[name] = model
    _versions[name] = version
    print(f"[ModelRegistry] ✓ {name} registered (version: {version})")


def get(name: str) -> Any | None:
    """Retrieve a loaded model."""
    return _registry.get(name)


def is_loaded(name: str) -> bool:
    return name in _registry


def get_status() -> Dict[str, dict]:
    """Return status of all known models."""
    return {
        name: {
            "loaded": name in _registry,
            "version": _versions.get(name, "not trained"),
            "description": desc,
        }
        for name, desc in MODEL_DESCRIPTIONS.items()
    }


def is_local_available() -> bool:
    """True if any trained models are loaded."""
    return any(is_loaded(m) for m in TRAINED_MODELS) or all(is_loaded(m) for m in CORE_MODELS)
