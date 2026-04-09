"""SBERT embedding utilities shared across modules 1/2/3/4.

Uses lazy-loaded sentence-transformers to avoid loading the model
at service startup (only when the first embed() call is made).
"""

from functools import lru_cache
from typing import List

import numpy as np

from .config import settings


@lru_cache(maxsize=1)
def _load_model():
    """Lazy-load SBERT. Heavy import — only executed on first use."""
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(settings.sbert_model_name)


def embed(text: str) -> np.ndarray:
    """Embed a single string into a 768-dim (or model-native) vector."""
    model = _load_model()
    vec = model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
    return vec.astype(np.float32)


def embed_batch(texts: List[str], batch_size: int = 32) -> np.ndarray:
    """Embed a list of strings. Returns shape (N, D)."""
    model = _load_model()
    vecs = model.encode(
        texts,
        batch_size=batch_size,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return vecs.astype(np.float32)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity for two L2-normalized vectors is just the dot product."""
    return float(np.dot(a, b))
