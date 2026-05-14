"""SBERT-backed retrieval over the 4,219 SLIIT papers.

Used by:
  • categorization      → "papers in this category"
  • plagiarism trends   → "actual SLIIT papers matching your query"
  • summarizer (future) → similar-paper suggestions

The first search call lazy-loads two artefacts:
  1. `papers_raw_sliit.json` — 4,219 records with id/title/authors/abstract/year/url/subject
  2. SBERT (SLIIT-tuned encoder if present, else `all-MiniLM-L6-v2`)

The corpus is then encoded once into a 4219×384 float32 matrix and cached
in-memory for the lifetime of the process. Encoding takes ~90 s the first
time; every subsequent query is a single normalised matmul (~30 ms).

Public API:
    is_loaded() -> bool
    load() -> bool
    find_related(query: str, top_k: int = 5, min_similarity: float = 0.0,
                 year_from: int | None = None, year_to: int | None = None,
                 subject_filter: str | None = None) -> list[dict]
    get_info() -> dict
"""

from __future__ import annotations

import json
import logging
import re
import threading
from pathlib import Path
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)

SERVICE_ROOT = Path(__file__).resolve().parent.parent.parent

PAPERS_PATH = SERVICE_ROOT / "data" / "papers_raw_sliit.json"
EMBEDDINGS_PATH = SERVICE_ROOT / "data" / "paper_embeddings.npy"
MODULE1_SBERT = SERVICE_ROOT / "models" / "sbert_plagiarism"
FALLBACK_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

_PAPERS: list[dict[str, Any]] | None = None
_EMBEDDINGS: np.ndarray | None = None
_MODEL = None
_MODEL_NAME = "unknown"
_LOAD_LOCK = threading.Lock()


def is_loaded() -> bool:
    return _EMBEDDINGS is not None and _PAPERS is not None


def _load_papers() -> bool:
    global _PAPERS
    if _PAPERS is not None:
        return True
    if not PAPERS_PATH.exists():
        logger.warning("[paper_index] %s not found", PAPERS_PATH)
        return False
    try:
        with open(PAPERS_PATH, encoding="utf-8") as f:
            data = json.load(f)
        _PAPERS = [p for p in data if (p.get("abstract") or "").strip()]
        logger.info("[paper_index] loaded %d papers (%d total in file)", len(_PAPERS), len(data))
        return True
    except Exception as e:
        logger.error("[paper_index] failed to load papers: %s", e)
        return False


def _load_model() -> bool:
    global _MODEL, _MODEL_NAME
    if _MODEL is not None:
        return True
    try:
        from sentence_transformers import SentenceTransformer
        _has_weights = (MODULE1_SBERT / "model.safetensors").exists() or (MODULE1_SBERT / "pytorch_model.bin").exists()
        if MODULE1_SBERT.exists() and _has_weights:
            _MODEL = SentenceTransformer(str(MODULE1_SBERT))
            _MODEL_NAME = "sbert_plagiarism (SLIIT fine-tuned)"
        else:
            _MODEL = SentenceTransformer(FALLBACK_MODEL)
            _MODEL_NAME = FALLBACK_MODEL
        return True
    except Exception as e:
        logger.error("[paper_index] failed to load SBERT: %s", e)
        return False


def load() -> bool:
    """Load papers + pre-computed embeddings + model for query encoding."""
    global _EMBEDDINGS
    if _EMBEDDINGS is not None:
        return True
    with _LOAD_LOCK:
        if _EMBEDDINGS is not None:
            return True
        if not _load_papers() or not _load_model():
            return False
        assert _PAPERS is not None

        if EMBEDDINGS_PATH.exists():
            emb = np.load(str(EMBEDDINGS_PATH))
            if emb.shape[0] == len(_PAPERS):
                _EMBEDDINGS = emb.astype("float32")
                logger.info("[paper_index] loaded pre-computed embeddings %s", _EMBEDDINGS.shape)
                return True
            logger.warning("[paper_index] embeddings shape mismatch (%d vs %d papers), re-encoding", emb.shape[0], len(_PAPERS))

        # Fallback: encode on the fly (slow, high RAM — only if .npy missing)
        logger.info("[paper_index] encoding %d abstracts on the fly…", len(_PAPERS))
        assert _MODEL is not None
        texts = [f"{(p.get('title') or '').strip()}. {(p.get('abstract') or '').strip()[:800]}" for p in _PAPERS]
        _EMBEDDINGS = _MODEL.encode(texts, batch_size=32, show_progress_bar=False,
                                    convert_to_numpy=True, normalize_embeddings=True).astype("float32")
        logger.info("[paper_index] index shape=%s", _EMBEDDINGS.shape)
        return True


def _normalize_subject(s: Any) -> str:
    if isinstance(s, list):
        s = " ".join(str(x) for x in s)
    return re.sub(r"\s+", " ", str(s or "").lower()).strip()


def find_related(
    query: str,
    top_k: int = 5,
    min_similarity: float = 0.15,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    subject_filter: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Return up to `top_k` SLIIT papers most similar to `query`.

    Each item: paper_id, title, authors, year, url, subject, similarity, abstract_excerpt.
    Results are filtered by year range and (optional) subject substring before ranking.
    """
    query = (query or "").strip()
    if len(query) < 3 or not load():
        return []
    assert _MODEL is not None and _PAPERS is not None and _EMBEDDINGS is not None

    qvec = _MODEL.encode(
        [query], convert_to_numpy=True, normalize_embeddings=True,
    ).astype("float32")[0]
    sims = _EMBEDDINGS @ qvec  # cosine because both are normalised

    # Apply filters by zeroing out non-matching rows
    sf = _normalize_subject(subject_filter) if subject_filter else None
    mask = np.ones(sims.shape, dtype=bool)
    for i, p in enumerate(_PAPERS):
        try:
            y = int(p.get("year")) if p.get("year") is not None else None
        except (TypeError, ValueError):
            y = None
        if year_from is not None and (y is None or y < year_from):
            mask[i] = False
            continue
        if year_to is not None and (y is None or y > year_to):
            mask[i] = False
            continue
        if sf:
            psubj = _normalize_subject(p.get("subject"))
            if sf not in psubj:
                mask[i] = False

    sims_filtered = np.where(mask, sims, -1.0)
    order = np.argsort(-sims_filtered)[: max(top_k, 1)]

    out: list[dict[str, Any]] = []
    for idx in order:
        s = float(sims_filtered[int(idx)])
        if s < min_similarity:
            break
        p = _PAPERS[int(idx)]
        abstract = (p.get("abstract") or "").strip()
        out.append({
            "paper_id": str(p.get("id") or p.get("handle") or idx),
            "title": (p.get("title") or "").strip(),
            "authors": p.get("authors") or [],
            "year": p.get("year"),
            "url": p.get("url") or p.get("source_url") or "",
            "subject": p.get("subject"),
            "similarity": round(s, 4),
            "abstract_excerpt": abstract[:280] + ("…" if len(abstract) > 280 else ""),
        })
    return out


def get_info() -> dict[str, Any]:
    if not load():
        return {"loaded": False}
    assert _PAPERS is not None and _EMBEDDINGS is not None
    return {
        "loaded": True,
        "n_papers": len(_PAPERS),
        "embedding_dim": int(_EMBEDDINGS.shape[1]),
        "base_model": _MODEL_NAME,
    }
