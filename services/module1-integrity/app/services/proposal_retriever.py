"""Local Proposal Retriever inference service.

Given a topic, finds the top-K most similar SLIIT papers and composes a
research proposal (problem statement, objectives, methodology, expected
outcomes) by retrieval + light templating — no API calls.

Public API:
    is_loaded() -> bool
    load() -> bool
    generate(topic: str, domain: str | None = None, top_k: int = 5) -> dict
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
INDEX_PATH = SERVICE_ROOT / "models" / "trained_proposal_retriever" / "proposal_index.pkl"
LOCAL_SBERT_DIR = SERVICE_ROOT / "models" / "sbert_plagiarism"
FALLBACK_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

_INDEX: Optional[dict[str, Any]] = None
_MODEL = None


def is_loaded() -> bool:
    return _INDEX is not None and _MODEL is not None


def load() -> bool:
    global _INDEX, _MODEL
    if is_loaded():
        return True
    if not INDEX_PATH.exists():
        logger.warning("[ProposalRetriever] index not found at %s", INDEX_PATH)
        return False
    try:
        with open(INDEX_PATH, "rb") as f:
            _INDEX = pickle.load(f)
        logger.info(
            "[ProposalRetriever] loaded index v%s — %d exemplars",
            _INDEX.get("version"), len(_INDEX["records"]),
        )
    except Exception as e:
        logger.error("[ProposalRetriever] failed to load index: %s", e)
        return False

    try:
        from sentence_transformers import SentenceTransformer
        if LOCAL_SBERT_DIR.exists() and any(LOCAL_SBERT_DIR.iterdir()):
            _MODEL = SentenceTransformer(str(LOCAL_SBERT_DIR))
        else:
            _MODEL = SentenceTransformer(FALLBACK_MODEL)
    except Exception as e:
        logger.error("[ProposalRetriever] failed to load SBERT: %s", e)
        _INDEX = None
        return False

    return True


def _encode_query(text: str) -> np.ndarray:
    assert _MODEL is not None
    vec = _MODEL.encode([text], convert_to_numpy=True, normalize_embeddings=True).astype("float32")
    return vec[0]


def _truncate(text: str, n: int) -> str:
    text = (text or "").strip()
    if len(text) <= n:
        return text
    cut = text[: n].rsplit(" ", 1)[0]
    return cut.rstrip(",.;: ") + "…"


def _compose_problem_statement(topic: str, domain: str | None, exemplars: list[dict[str, Any]]) -> str:
    """Stitch a problem statement using top exemplar's problem-statement
    sentence + topic anchoring."""
    domain_clause = f" within the domain of {domain}" if domain else ""
    if exemplars:
        seed = exemplars[0].get("problem_statement") or exemplars[0].get("abstract", "")
        seed = _truncate(seed, 350)
        return (
            f"This research investigates {topic}{domain_clause}. Prior SLIIT research "
            f"by {_format_authors(exemplars[0].get('authors'))} ({exemplars[0].get('year','n/a')}) "
            f"observed that: \"{seed}\" Building on these findings, this study aims to "
            f"address the remaining limitations and extend the contribution to {topic}."
        )
    return (
        f"This research investigates {topic}{domain_clause}, motivated by gaps "
        f"identified in prior literature."
    )


def _compose_objectives(topic: str, exemplars: list[dict[str, Any]]) -> list[str]:
    """Three to five objectives. Mix generic SLR-style with exemplar-derived."""
    objectives: list[str] = [
        f"Conduct a systematic literature review on {topic}, mapping existing approaches and gaps.",
        f"Identify methodological and empirical gaps in current research on {topic}.",
    ]
    # Pull 1-2 verbs from exemplars' methodology hints
    seen: set[str] = set()
    for ex in exemplars[:3]:
        snippet = (ex.get("methodology_text") or ex.get("abstract") or "").strip()
        if not snippet:
            continue
        m = re.search(r"\b(propose|develop|design|evaluate|implement|analyze|assess|construct)\b[^.]{5,160}\.",
                      snippet, re.IGNORECASE)
        if m:
            sent = m.group(0).strip()
            key = sent.lower()[:80]
            if key in seen:
                continue
            seen.add(key)
            objectives.append(f"Adapt SLIIT precedent: {_truncate(sent, 180)}")
        if len(objectives) >= 5:
            break
    if len(objectives) < 4:
        objectives.append(f"Validate the proposed approach for {topic} via empirical evaluation.")
    return objectives[:5]


def _compose_methodology(topic: str, exemplars: list[dict[str, Any]]) -> str:
    parts = [
        f"This study adopts a mixed-methods design tailored to {topic}.",
    ]
    method_signals: list[str] = []
    for ex in exemplars[:5]:
        snippet = (ex.get("methodology_text") or "").strip()
        if not snippet:
            continue
        method_signals.append(_truncate(snippet, 220))
    if method_signals:
        parts.append("Building on prior SLIIT work, the methodology incorporates: ")
        parts.append(" ".join(method_signals[:3]))
    parts.append(
        "Data collection will follow established practices (literature review, "
        "expert interviews, and quantitative evaluation), with statistical and "
        "thematic analyses applied to validate findings."
    )
    return " ".join(parts)


def _compose_expected_outcomes(topic: str, exemplars: list[dict[str, Any]]) -> str:
    contrib = [
        f"Empirical evidence advancing the understanding of {topic}.",
        "A reproducible methodology grounded in SLIIT precedent.",
        "Practical recommendations for future researchers and practitioners.",
    ]
    if exemplars:
        contrib.append(
            f"Direct extension of {len(exemplars)} prior SLIIT studies, with explicit "
            f"comparison to their reported limitations."
        )
    return " ".join(contrib)


def _format_authors(authors: Any) -> str:
    if not authors:
        return "prior authors"
    if isinstance(authors, list):
        names = [str(a) for a in authors[:2]]
        if len(authors) > 2:
            names.append("et al.")
        return ", ".join(names)
    return str(authors)


def generate(topic: str, domain: str | None = None, top_k: int = 5) -> dict[str, Any]:
    if not load():
        return {"loaded": False}
    assert _INDEX is not None and _MODEL is not None

    query = topic if not domain else f"{topic} ({domain})"
    qvec = _encode_query(query)
    embeddings: np.ndarray = _INDEX["embeddings"]
    records: list[dict[str, Any]] = _INDEX["records"]

    sims = embeddings @ qvec
    order = np.argsort(-sims)[:top_k]
    exemplars = []
    for idx in order:
        rec = records[int(idx)]
        exemplars.append({**rec, "similarity": round(float(sims[idx]), 3)})

    proposal = {
        "loaded": True,
        "problem_statement": _compose_problem_statement(topic, domain, exemplars),
        "objectives": _compose_objectives(topic, exemplars),
        "methodology": _compose_methodology(topic, exemplars),
        "expected_outcomes": _compose_expected_outcomes(topic, exemplars),
        "retrieved_papers": [
            {
                "paper_id": ex.get("paper_id", ""),
                "title": ex.get("title", ""),
                "authors": ex.get("authors", []),
                "year": ex.get("year"),
                "url": ex.get("url", ""),
                "similarity": ex["similarity"],
            }
            for ex in exemplars
        ],
        "model_version": _INDEX.get("version", "unknown"),
        "base_model": _INDEX.get("base_model", "unknown"),
    }
    return proposal


def get_model_info() -> dict[str, Any]:
    if not load():
        return {"loaded": False, "error": "Index file not found — run train_proposal_retriever.py"}
    assert _INDEX is not None
    return {
        "loaded": True,
        "version": _INDEX.get("version", "unknown"),
        "base_model": _INDEX.get("base_model", "unknown"),
        "embedding_dim": _INDEX.get("embedding_dim"),
        "n_exemplars": len(_INDEX["records"]),
    }
