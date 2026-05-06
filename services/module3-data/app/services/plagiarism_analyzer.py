"""Plagiarism trend analyzer — local model service.

Two operations:

1. **search_trends(query, top_k)** — given a topic / category in free text,
   find the most similar SLIIT topic-buckets and return their precomputed
   plagiarism trend rows (yearly avg/max/p95 similarity, flagged pairs, etc.).

2. **compare_papers(text_a, text_b)** — for two arbitrary paper texts,
   compute:
     - SBERT cosine similarity over the full text
     - n-gram overlap (4-grams, Jaccard)
     - top-K most similar sentence pairs (with their indices)
     - aggregate plagiarism risk level

Both are deterministic and CPU-only.

Public API:
    is_loaded() -> bool
    load() -> bool
    search_trends(query: str, top_k: int = 5) -> dict
    compare_papers(text_a: str, text_b: str, top_pairs: int = 5) -> dict
    get_model_info() -> dict
"""

from __future__ import annotations

import logging
import pickle
import re
from pathlib import Path
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)

SERVICE_ROOT = Path(__file__).resolve().parent.parent.parent
PROJECT_ROOT = SERVICE_ROOT.parent.parent

INDEX_PATH = SERVICE_ROOT / "models" / "trained_plagiarism_analyzer" / "trend_index.pkl"
MODULE1_SBERT = PROJECT_ROOT / "services" / "module1-integrity" / "models" / "sbert_plagiarism"
FALLBACK_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

_INDEX: Optional[dict[str, Any]] = None
_MODEL = None
_MODEL_NAME: str = "unknown"

# Risk thresholds (cosine similarity)
RISK_LOW = 0.30
RISK_MED = 0.60
RISK_HIGH = 0.80


def is_loaded() -> bool:
    return _MODEL is not None


def _load_sbert() -> bool:
    global _MODEL, _MODEL_NAME
    if _MODEL is not None:
        return True
    try:
        from sentence_transformers import SentenceTransformer
        if MODULE1_SBERT.exists() and any(MODULE1_SBERT.iterdir()):
            _MODEL = SentenceTransformer(str(MODULE1_SBERT))
            _MODEL_NAME = "sbert_plagiarism (SLIIT fine-tuned)"
        else:
            _MODEL = SentenceTransformer(FALLBACK_MODEL)
            _MODEL_NAME = FALLBACK_MODEL
        return True
    except Exception as e:
        logger.error("[PlagiarismAnalyzer] failed to load SBERT: %s", e)
        return False


def load() -> bool:
    """Load the trend index AND the SBERT model. Either alone is OK for some
    operations: search_trends needs both, compare_papers needs only SBERT."""
    global _INDEX
    sbert_ok = _load_sbert()
    if _INDEX is None and INDEX_PATH.exists():
        try:
            with open(INDEX_PATH, "rb") as f:
                _INDEX = pickle.load(f)
            logger.info(
                "[PlagiarismAnalyzer] loaded index v%s — %d topics",
                _INDEX.get("version"), len(_INDEX["topics"]),
            )
        except Exception as e:
            logger.error("[PlagiarismAnalyzer] failed to load index: %s", e)
    return sbert_ok


# ─────────────────────────────────────────────────────────────────────────────
# Trend search
# ─────────────────────────────────────────────────────────────────────────────


def search_trends(query: str, top_k: int = 5) -> dict[str, Any]:
    if not load():
        return {"loaded": False, "matches": []}
    if _INDEX is None:
        return {"loaded": False, "error": "trend index missing", "matches": []}
    assert _MODEL is not None

    qvec = _MODEL.encode([query], convert_to_numpy=True, normalize_embeddings=True).astype("float32")[0]
    sims = _INDEX["embeddings"] @ qvec
    order = np.argsort(-sims)[:top_k]

    matches = []
    for idx in order:
        meta = _INDEX["topic_meta"][int(idx)]
        matches.append({
            "topic": meta["topic"],
            "similarity": round(float(sims[int(idx)]), 4),
            "n_records": meta["n_records"],
            "n_papers_total": meta["n_papers_total"],
            "avg_similarity_overall": meta["avg_similarity_overall"],
            "max_avg_similarity": meta["max_avg_similarity"],
            "n_high_similarity_pairs_total": meta["n_high_similarity_pairs_total"],
            "latest_year": meta["latest_year"],
            "latest_trend_direction": meta["latest_trend_direction"],
            "yearly": meta["yearly"],
        })

    return {
        "loaded": True,
        "matches": matches,
        "total_topics": len(_INDEX["topics"]),
        "model_version": _INDEX.get("version", "unknown"),
        "base_model": _INDEX.get("base_model", "unknown"),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Pair comparison
# ─────────────────────────────────────────────────────────────────────────────


def _ngrams(text: str, n: int = 4) -> set[str]:
    text = re.sub(r"\s+", " ", (text or "").lower()).strip()
    tokens = re.findall(r"[a-z0-9]+", text)
    return {" ".join(tokens[i : i + n]) for i in range(len(tokens) - n + 1)} if len(tokens) >= n else set()


def _split_sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text or "").strip()
    if not text:
        return []
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'\(])", text)
    return [p.strip() for p in parts if 20 <= len(p) <= 600][:300]


def _risk_level(sim: float) -> str:
    if sim >= RISK_HIGH:
        return "high"
    if sim >= RISK_MED:
        return "medium"
    if sim >= RISK_LOW:
        return "low"
    return "minimal"


def compare_papers(text_a: str, text_b: str, top_pairs: int = 5) -> dict[str, Any]:
    """Pairwise plagiarism analysis of two paper texts."""
    if not _load_sbert():
        return {"loaded": False}
    assert _MODEL is not None

    text_a = (text_a or "").strip()
    text_b = (text_b or "").strip()
    if not text_a or not text_b:
        return {"loaded": True, "error": "Both texts must be non-empty"}

    # Document-level cosine via centroid embedding
    emb_a, emb_b = _MODEL.encode(
        [text_a, text_b],
        batch_size=2,
        convert_to_numpy=True,
        normalize_embeddings=True,
    ).astype("float32")
    doc_sim = float(np.dot(emb_a, emb_b))

    # 4-gram overlap
    a_ng = _ngrams(text_a, 4)
    b_ng = _ngrams(text_b, 4)
    if a_ng and b_ng:
        inter = len(a_ng & b_ng)
        union = len(a_ng | b_ng)
        ngram_jaccard = inter / max(1, union)
        ngram_overlap_a = inter / max(1, len(a_ng))
        ngram_overlap_b = inter / max(1, len(b_ng))
    else:
        ngram_jaccard = 0.0
        ngram_overlap_a = 0.0
        ngram_overlap_b = 0.0

    # Sentence-level similarity matrix → top pairs
    sents_a = _split_sentences(text_a)
    sents_b = _split_sentences(text_b)
    flagged_pairs: list[dict[str, Any]] = []
    if sents_a and sents_b:
        sa = _MODEL.encode(sents_a, batch_size=32, convert_to_numpy=True, normalize_embeddings=True).astype("float32")
        sb = _MODEL.encode(sents_b, batch_size=32, convert_to_numpy=True, normalize_embeddings=True).astype("float32")
        M = sa @ sb.T
        # Find top_pairs sentence-pair similarities
        flat = M.ravel()
        # Get indices of top values, then map back
        if flat.size:
            cnt = min(top_pairs, flat.size)
            idx = np.argpartition(-flat, cnt - 1)[:cnt]
            idx = idx[np.argsort(-flat[idx])]
            for k in idx:
                i, j = int(k // M.shape[1]), int(k % M.shape[1])
                sim_val = float(M[i, j])
                if sim_val < 0.5:
                    break
                flagged_pairs.append({
                    "similarity": round(sim_val, 4),
                    "sentence_a": sents_a[i],
                    "sentence_b": sents_b[j],
                    "index_a": i,
                    "index_b": j,
                })

    # Aggregate risk score: SBERT similarity catches paraphrasing (the more
    # common form of academic plagiarism), so weight it more heavily than
    # exact n-gram overlap. n-grams remain useful as a copy-paste tripwire.
    risk_score = round(0.75 * doc_sim + 0.25 * ngram_jaccard, 4)
    risk_level = _risk_level(risk_score)

    return {
        "loaded": True,
        "document_similarity": round(doc_sim, 4),
        "ngram_jaccard": round(ngram_jaccard, 4),
        "ngram_overlap_in_a": round(ngram_overlap_a, 4),
        "ngram_overlap_in_b": round(ngram_overlap_b, 4),
        "risk_score": risk_score,
        "risk_level": risk_level,
        "flagged_pairs": flagged_pairs,
        "n_sentences_a": len(sents_a),
        "n_sentences_b": len(sents_b),
        "model_version": _MODEL_NAME,
    }


def get_model_info() -> dict[str, Any]:
    info = {
        "sbert_loaded": _load_sbert(),
        "sbert_version": _MODEL_NAME if _MODEL is not None else None,
        "trend_index_loaded": False,
    }
    if INDEX_PATH.exists():
        # ensure INDEX is loaded
        load()
    if _INDEX is not None:
        info["trend_index_loaded"] = True
        info["n_topics"] = len(_INDEX["topics"])
        info["index_version"] = _INDEX.get("version")
    return info
