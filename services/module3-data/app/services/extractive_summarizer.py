"""Extractive point-wise summarizer.

Algorithm:
  1. Sentence-split the input.
  2. Encode every sentence with SBERT (the SLIIT-tuned encoder if available).
  3. Score each sentence by:
        centroid_sim   * 0.55   ← topical relevance
      + position_score * 0.20   ← lead-bias
      + length_score   * 0.10   ← penalise extremes
      + novelty        * 0.15   ← MMR-like redundancy penalty
  4. Greedy-pick the top sentences (more for "detailed", fewer for "quick").
  5. Categorise each picked sentence into one of:
        background | objective | methodology | results | limitations | conclusion
  6. Return:
        - flat `summary` string (joined)
        - `key_points` list ordered by category, each with category + text
        - `grouped_points` dict keyed by category for grouped UI rendering

Why extractive (and not BART)?
  - BART weights for the SLIIT domain are not in repo.
  - Extractive is *grounded* — every point is verbatim from the paper, so
    there is zero hallucination risk for academic use.
  - Cost: ~80 ms per paper on CPU vs ~5 s for BART.

Public API:
    is_loaded() -> bool
    load() -> bool
    summarize(text: str, length: str = "standard") -> dict
    get_model_info() -> dict
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)

SERVICE_ROOT = Path(__file__).resolve().parent.parent.parent
PROJECT_ROOT = SERVICE_ROOT.parent.parent
MODULE1_SBERT = PROJECT_ROOT / "services" / "module1-integrity" / "models" / "sbert_plagiarism"
FALLBACK_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Length presets — number of *key points* to extract.
# "short"/"medium"/"detailed" kept as aliases for backwards compatibility.
LENGTHS: dict[str, int] = {
    "quick":    5,
    "short":    5,    # alias of quick
    "standard": 9,
    "medium":   9,    # alias of standard
    "detailed": 14,
    "extensive": 18,
}

MAX_SENTENCES = 250

# Heuristic keyword cues for categorising a sentence by section. The order of
# checks matters — we evaluate from most-specific to least-specific.
_CATEGORY_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("conclusion", re.compile(
        r"\b(in (conclusion|summary)|we conclude|to (sum up|conclude)|overall,|"
        r"this (paper|study|work) (has shown|demonstrates|presents))\b",
        re.IGNORECASE,
    )),
    ("limitations", re.compile(
        r"\b(however,?|limitation|drawback|challenge|future (work|research|direction)|"
        r"further (research|study|investigation)|need(s|ed) further|not yet|remains? "
        r"(an open|unclear|unsolved))\b",
        re.IGNORECASE,
    )),
    ("results", re.compile(
        r"\b(result|achiev(e|ed|ing)|accuracy|f1|precision|recall|outperform|"
        r"improve(s|d)?|increase(s|d)?|decrease(s|d)?|we (find|found|observe|show)|"
        r"the experiments? (show|reveal|demonstrate)|performance|baseline)\b",
        re.IGNORECASE,
    )),
    ("methodology", re.compile(
        r"\b(method(ology)?|approach|algorithm|framework|architecture|model|"
        r"we (use|employ|apply|adopt|propose|develop|implement|train|build|design)|"
        r"experiment|simulation|evaluat|dataset|corpus|interview|survey|"
        r"thematic analysis|machine learning|deep learning|neural network|"
        r"convolutional|transformer|svm|random forest|regression)\b",
        re.IGNORECASE,
    )),
    ("objective", re.compile(
        r"\b(this (paper|study|research|work|article)|the (aim|goal|purpose|"
        r"objective) of|we (aim|seek|propose|present|investigate|explore|examine|"
        r"address|introduce))\b",
        re.IGNORECASE,
    )),
    ("background", re.compile(
        r"\b(recently,?|in recent years|currently,?|the (literature|field)|"
        r"prior (work|research|studies)|previous (work|research|studies)|"
        r"existing (research|approaches|systems)|background|introduction)\b",
        re.IGNORECASE,
    )),
]

# Display order (and label) for the categories.
CATEGORY_ORDER = ["background", "objective", "methodology", "results", "limitations", "conclusion"]
CATEGORY_LABELS = {
    "background":   "Background",
    "objective":    "Objective",
    "methodology":  "Methodology",
    "results":      "Findings & Results",
    "limitations":  "Limitations & Future Work",
    "conclusion":   "Conclusion",
    "general":      "Other key points",
}


_MODEL = None
_MODEL_NAME: str = "unknown"


def is_loaded() -> bool:
    return _MODEL is not None


def load() -> bool:
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
        logger.info("[ExtractiveSummarizer] loaded SBERT %s", _MODEL_NAME)
        return True
    except Exception as e:
        logger.error("[ExtractiveSummarizer] failed to load SBERT: %s", e)
        return False


def _split_sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text or "").strip()
    if not text:
        return []
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'\(])", text)
    out: list[str] = []
    for p in parts:
        p = p.strip()
        if 20 <= len(p) <= 600:
            out.append(p)
    return out[:MAX_SENTENCES]


def _length_score(sent: str) -> float:
    n = len(sent)
    if 60 <= n <= 250:
        return 1.0
    if n < 60:
        return n / 60
    if n > 400:
        return max(0.0, 1.0 - (n - 400) / 400)
    return max(0.0, 1.0 - (n - 250) / 200)


def _position_score(idx: int, total: int) -> float:
    if total <= 1:
        return 1.0
    rel = idx / max(1, total - 1)
    if rel <= 0.20:
        return 1.0
    if rel >= 0.90:
        return 0.7
    if rel >= 0.75:
        return 0.5
    return max(0.2, 1.0 - rel)


def _categorize(sent: str, position_rel: float) -> str:
    """Classify a sentence into a section category. Falls back to position-based
    inference: first 15% → background, last 15% → conclusion, otherwise general."""
    for cat, pat in _CATEGORY_PATTERNS:
        if pat.search(sent):
            return cat
    if position_rel < 0.15:
        return "background"
    if position_rel > 0.85:
        return "conclusion"
    return "general"


def summarize(text: str, length: str = "standard") -> dict[str, Any]:
    """Return an extractive point-wise summary of `text`.

    Args:
        text   : the full document text (paper, abstract, etc.)
        length : one of `quick | short | standard | medium | detailed | extensive`
                 Aliases: short=quick, medium=standard.
    """
    if not load():
        return {"loaded": False, "summary": "", "sentences": [], "key_points": [], "grouped_points": {}}
    assert _MODEL is not None

    sents = _split_sentences(text)
    if len(sents) <= 2:
        single = " ".join(sents)
        kp = [{"category": "general", "category_label": CATEGORY_LABELS["general"], "text": s} for s in sents]
        return {
            "loaded": True,
            "summary": single,
            "sentences": sents,
            "key_points": kp,
            "grouped_points": {"general": kp} if kp else {},
            "n_sentences_input": len(sents),
            "n_sentences_output": len(sents),
            "compression_ratio": 1.0 if single else 0.0,
            "model_version": _MODEL_NAME,
        }

    embs = _MODEL.encode(sents, batch_size=32, convert_to_numpy=True, normalize_embeddings=True).astype("float32")
    centroid = embs.mean(axis=0)
    centroid /= max(1e-9, float(np.linalg.norm(centroid)))
    centroid_sim = embs @ centroid

    n = len(sents)
    pos = np.array([_position_score(i, n) for i in range(n)], dtype="float32")
    lens = np.array([_length_score(s) for s in sents], dtype="float32")
    base = 0.55 * centroid_sim + 0.20 * pos + 0.10 * lens

    target_n = LENGTHS.get(length, 9)
    target_n = min(target_n, n)

    # Greedy MMR selection
    selected: list[int] = []
    while len(selected) < target_n:
        best_score = -1e9
        best_idx = -1
        for i in range(n):
            if i in selected:
                continue
            redundancy = float(np.max(embs[selected] @ embs[i])) if selected else 0.0
            score = float(base[i] - 0.15 * redundancy)
            if score > best_score:
                best_score = score
                best_idx = i
        if best_idx == -1:
            break
        selected.append(best_idx)

    selected.sort()
    summary_sents = [sents[i] for i in selected]
    summary_text = " ".join(summary_sents)

    # Categorise each selected sentence
    key_points: list[dict[str, str]] = []
    for i in selected:
        sent = sents[i]
        rel = i / max(1, n - 1)
        cat = _categorize(sent, rel)
        key_points.append({
            "category": cat,
            "category_label": CATEGORY_LABELS.get(cat, cat.title()),
            "text": sent,
        })

    # Build grouped dict in display order, only including non-empty buckets
    grouped: dict[str, list[dict[str, str]]] = {}
    for cat in CATEGORY_ORDER + ["general"]:
        items = [kp for kp in key_points if kp["category"] == cat]
        if items:
            grouped[cat] = items

    # Re-order key_points to match grouped display order
    ordered_points: list[dict[str, str]] = []
    for cat in CATEGORY_ORDER + ["general"]:
        ordered_points.extend(grouped.get(cat, []))

    return {
        "loaded": True,
        "summary": summary_text,
        "sentences": summary_sents,
        "key_points": ordered_points,
        "grouped_points": grouped,
        "selected_indices": selected,
        "n_sentences_input": n,
        "n_sentences_output": len(selected),
        "compression_ratio": round(len(summary_text) / max(1, len(text)), 3),
        "model_version": _MODEL_NAME,
    }


def get_model_info() -> dict[str, Any]:
    if not load():
        return {"loaded": False, "error": "SBERT model not available"}
    return {
        "loaded": True,
        "version": _MODEL_NAME,
        "algorithm": "extractive (centroid + lead-bias + MMR + categorisation)",
        "supported_lengths": list(LENGTHS.keys()),
        "categories": CATEGORY_ORDER,
    }
