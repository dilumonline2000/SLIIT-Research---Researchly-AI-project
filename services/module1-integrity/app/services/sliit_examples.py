"""Find SLIIT papers similar to a user's citation/topic.

Reuses the SBERT index built for the proposal retriever (3,858 SLIIT papers).
Adds a tiny in-memory cache so repeated lookups are sub-millisecond.

Public API:
    similar_papers(query: str, top_k: int = 5) -> list[dict]
"""

from __future__ import annotations

import logging
import pickle
from pathlib import Path
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)

SERVICE_ROOT = Path(__file__).resolve().parent.parent.parent
INDEX_PATH = SERVICE_ROOT / "models" / "trained_proposal_retriever" / "proposal_index.pkl"
LOCAL_SBERT_DIR = SERVICE_ROOT / "models" / "sbert_plagiarism"
FALLBACK_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

_INDEX: Optional[dict[str, Any]] = None
_MODEL = None


def _load() -> bool:
    global _INDEX, _MODEL
    if _INDEX is not None and _MODEL is not None:
        return True
    if not INDEX_PATH.exists():
        logger.warning("[sliit_examples] index missing at %s", INDEX_PATH)
        return False
    try:
        with open(INDEX_PATH, "rb") as f:
            _INDEX = pickle.load(f)
    except Exception as e:
        logger.error("[sliit_examples] failed to load index: %s", e)
        return False
    try:
        from sentence_transformers import SentenceTransformer
        if LOCAL_SBERT_DIR.exists() and any(LOCAL_SBERT_DIR.iterdir()):
            _MODEL = SentenceTransformer(str(LOCAL_SBERT_DIR))
        else:
            _MODEL = SentenceTransformer(FALLBACK_MODEL)
        return True
    except Exception as e:
        logger.error("[sliit_examples] failed to load SBERT: %s", e)
        return False


def similar_papers(query: str, top_k: int = 5) -> list[dict[str, Any]]:
    """Return up to `top_k` SLIIT papers most similar to `query`.

    Each result has: paper_id, title, authors, year, url, similarity, abstract_excerpt.
    """
    query = (query or "").strip()
    if not query or not _load():
        return []
    assert _INDEX is not None and _MODEL is not None

    qvec = _MODEL.encode([query], convert_to_numpy=True, normalize_embeddings=True).astype("float32")[0]
    sims: np.ndarray = _INDEX["embeddings"] @ qvec
    order = np.argsort(-sims)[:top_k]

    out: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = _INDEX["records"]
    for idx in order:
        r = records[int(idx)]
        abstract = (r.get("abstract") or "").strip()
        out.append({
            "paper_id": r.get("paper_id", ""),
            "title": r.get("title", ""),
            "authors": r.get("authors", []),
            "year": r.get("year"),
            "url": r.get("url", ""),
            "similarity": round(float(sims[int(idx)]), 3),
            "abstract_excerpt": abstract[:280] + ("…" if len(abstract) > 280 else ""),
        })
    return out
