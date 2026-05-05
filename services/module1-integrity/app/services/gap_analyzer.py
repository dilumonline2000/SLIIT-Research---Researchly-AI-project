"""Local Gap Analyzer inference service.

Given a topic / proposal text, returns the top-K research gaps from the SLIIT
corpus, scored by topical similarity and clustered to remove near-duplicates.

Loaded lazily on first call. Uses:
  models/trained_gap_analyzer/gap_index.pkl
  models/sbert_plagiarism/  (or all-MiniLM-L6-v2 fallback)

Public API:
    is_loaded() -> bool
    load() -> bool
    analyze(topic: str, top_k: int = 8, min_similarity: float = 0.25) -> dict
    get_model_info() -> dict
"""

from __future__ import annotations

import logging
import pickle
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)

SERVICE_ROOT = Path(__file__).resolve().parent.parent.parent
INDEX_PATH = SERVICE_ROOT / "models" / "trained_gap_analyzer" / "gap_index.pkl"
LOCAL_SBERT_DIR = SERVICE_ROOT / "models" / "sbert_plagiarism"
FALLBACK_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Cluster gaps if their cosine similarity is above this threshold.
DEDUP_THRESHOLD = 0.78

_INDEX: Optional[dict[str, Any]] = None
_MODEL = None  # SentenceTransformer instance


def is_loaded() -> bool:
    return _INDEX is not None and _MODEL is not None


def load() -> bool:
    """Load index + SBERT model. Returns True on success."""
    global _INDEX, _MODEL
    if is_loaded():
        return True
    if not INDEX_PATH.exists():
        logger.warning("[GapAnalyzer] index not found at %s", INDEX_PATH)
        return False
    try:
        with open(INDEX_PATH, "rb") as f:
            _INDEX = pickle.load(f)
        logger.info(
            "[GapAnalyzer] loaded index v%s — %d gaps, dim=%d",
            _INDEX.get("version"), len(_INDEX["records"]), _INDEX.get("embedding_dim", -1),
        )
    except Exception as e:
        logger.error("[GapAnalyzer] failed to load index: %s", e)
        return False

    try:
        from sentence_transformers import SentenceTransformer
        if LOCAL_SBERT_DIR.exists() and any(LOCAL_SBERT_DIR.iterdir()):
            _MODEL = SentenceTransformer(str(LOCAL_SBERT_DIR))
            logger.info("[GapAnalyzer] using fine-tuned SBERT %s", LOCAL_SBERT_DIR)
        else:
            _MODEL = SentenceTransformer(FALLBACK_MODEL)
            logger.info("[GapAnalyzer] using base SBERT %s", FALLBACK_MODEL)
    except Exception as e:
        logger.error("[GapAnalyzer] failed to load SBERT: %s", e)
        _INDEX = None
        return False

    return True


def _encode_query(text: str) -> np.ndarray:
    assert _MODEL is not None
    vec = _MODEL.encode(
        [text], convert_to_numpy=True, normalize_embeddings=True
    ).astype("float32")
    return vec[0]


def _cluster_top_results(
    candidates: list[dict[str, Any]], embeddings: np.ndarray
) -> list[dict[str, Any]]:
    """Greedy near-duplicate clustering: keep first, drop anything very similar
    to an already-kept gap. Embeddings parallel to `candidates`."""
    kept_idx: list[int] = []
    kept_embs: list[np.ndarray] = []
    for i, cand in enumerate(candidates):
        emb = embeddings[i]
        is_dup = False
        for ke in kept_embs:
            if float(np.dot(emb, ke)) >= DEDUP_THRESHOLD:
                is_dup = True
                break
        if not is_dup:
            kept_idx.append(i)
            kept_embs.append(emb)
    return [candidates[i] for i in kept_idx]


def _recency_score(year: Any) -> float:
    """Newer paper → lower recency_score (less stale).
    Older paper → higher recency_score (gap is older / more stale)."""
    try:
        y = int(year)
    except (TypeError, ValueError):
        return 0.5
    now = datetime.now().year
    diff = max(0, now - y)
    # 0 yrs → 0.20, 5 yrs → 0.50, 10+ yrs → 0.95
    return round(min(0.95, 0.20 + (diff / 12)), 3)


def _gap_score(similarity: float, gap_type: str) -> float:
    """Combine similarity with gap-type weighting. `research_gap` and
    `not_investigated` are stronger signals than generic `limitation`."""
    weight = {
        "research_gap": 1.10,
        "not_investigated": 1.08,
        "unexplored": 1.06,
        "more_needed": 1.04,
        "future_work": 1.02,
        "scarcity": 1.00,
        "limitation": 0.95,
    }.get(gap_type, 1.0)
    return round(min(1.0, similarity * weight), 3)


def _novelty_score(year: Any, similarity: float) -> float:
    """High when the gap is recent AND highly similar to the query — i.e. an
    actively-discussed open problem."""
    try:
        y = int(year)
    except (TypeError, ValueError):
        y = 2018
    now = datetime.now().year
    recency = max(0.0, 1.0 - (now - y) / 10)
    return round(min(1.0, 0.5 * recency + 0.5 * similarity), 3)


def analyze(topic: str, top_k: int = 8, min_similarity: float = 0.25) -> dict[str, Any]:
    """Return ranked research gaps for a topic, grounded in SLIIT papers."""
    if not load():
        return {"loaded": False, "gaps": [], "total_papers_analyzed": 0}
    assert _INDEX is not None and _MODEL is not None

    query_vec = _encode_query(topic)
    embeddings: np.ndarray = _INDEX["embeddings"]
    records: list[dict[str, Any]] = _INDEX["records"]

    sims = embeddings @ query_vec  # cosine because both already normalized
    order = np.argsort(-sims)

    # Take top 4*K then dedupe down to K
    pool = min(len(order), max(40, top_k * 5))
    top_idx = order[:pool]

    candidates: list[dict[str, Any]] = []
    for idx in top_idx:
        sim = float(sims[idx])
        if sim < min_similarity:
            continue
        rec = records[int(idx)]
        candidates.append({
            "topic": rec.get("topic") or rec.get("title", "")[:80],
            "description": rec["gap_text"],
            "gap_type": rec.get("gap_type", "limitation"),
            "gap_score": _gap_score(sim, rec.get("gap_type", "limitation")),
            "recency_score": _recency_score(rec.get("year")),
            "novelty_score": _novelty_score(rec.get("year"), sim),
            "similarity": round(sim, 3),
            "supporting_paper": {
                "paper_id": rec.get("paper_id", ""),
                "title": rec.get("title", ""),
                "authors": rec.get("authors", []),
                "year": rec.get("year"),
                "url": rec.get("url", ""),
            },
        })

    # Dedupe in embedding space
    cand_vecs = embeddings[top_idx[: len(candidates)]]
    deduped = _cluster_top_results(candidates, cand_vecs)
    final = sorted(deduped, key=lambda g: g["gap_score"], reverse=True)[:top_k]

    return {
        "loaded": True,
        "gaps": final,
        "total_papers_analyzed": int((sims > 0.0).sum()),
        "total_corpus_size": len(records),
        "model_version": _INDEX.get("version", "unknown"),
        "base_model": _INDEX.get("base_model", "unknown"),
    }


def get_model_info() -> dict[str, Any]:
    if not load():
        return {"loaded": False, "error": "Index file not found — run train_gap_analyzer.py"}
    assert _INDEX is not None
    return {
        "loaded": True,
        "version": _INDEX.get("version", "unknown"),
        "base_model": _INDEX.get("base_model", "unknown"),
        "embedding_dim": _INDEX.get("embedding_dim"),
        "n_gaps": len(_INDEX["records"]),
        "n_unique_papers": len({r.get("paper_id") for r in _INDEX["records"] if r.get("paper_id")}),
    }
