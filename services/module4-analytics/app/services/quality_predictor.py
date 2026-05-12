"""Quality Score Predictor inference service.

Loads trained XGBoost models and predicts quality dimensions for any paper text.
"""

from __future__ import annotations

import logging
import pickle
import re
from pathlib import Path
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

# Model path
_SERVICE_ROOT = Path(__file__).parent.parent.parent
_MODEL_PATH = _SERVICE_ROOT / "models" / "trained_quality_predictor" / "quality_models.pkl"

_MODEL_DATA: Optional[dict] = None


# Original keyword set — kept unchanged so extract_features() feeds the
# XGBoost model exactly the same feature distribution it was trained on.
METHODOLOGY_KEYWORDS = [
    "experiment", "survey", "case study", "simulation", "prototype",
    "evaluation", "benchmark", "dataset", "statistical", "hypothesis",
    "mixed method", "qualitative", "quantitative", "systematic review",
    "regression", "interview", "questionnaire", "thematic analysis",
    "structural equation", "factor analysis", "anova", "correlation",
    "machine learning", "deep learning", "model", "algorithm",
]

# Strict research-specific methodology terms used ONLY in the heuristic scorer.
# These are terms unique to research papers and NOT common in forms/rubrics/reports.
_STRONG_METHOD_KWS = [
    # Experimental design
    "experiment", "survey instrument", "case study", "simulation",
    "benchmark", "dataset", "hypothesis", "systematic review",
    "regression", "questionnaire", "thematic analysis",
    "structural equation", "factor analysis", "anova", "correlation",
    # ML / AI specific
    "machine learning", "deep learning", "neural network", "random forest",
    "convolutional", "transformer", "fine-tun", "pre-train",
    # Outcome measurement (research-specific phrases, not single generic words)
    "classification accuracy", "detection accuracy", "precision recall",
    "f1 score", "f1-score", "cross-validation", "training data",
    "test set", "training set", "ground truth", "confusion matrix",
    "mean absolute error", "root mean square",
    # Action phrases unique to research writing
    "we propose", "we present a", "we introduce", "we investigate",
    "this paper presents", "this study", "proposed model", "proposed method",
    "proposed framework", "proposed algorithm", "experimental results",
    "results demonstrate", "results show",
]

# Phrases that strongly indicate original research writing.
_RESEARCH_PHRASES = [
    "this paper", "this study", "this work", "we propose", "we present",
    "we introduce", "we investigate", "we develop", "we design",
    "our approach", "our method", "our model", "our framework",
    "our results", "our findings", "results show", "results indicate",
    "we demonstrate", "we evaluate", "we analyze", "we show that",
    "experimental results", "in this paper", "in this work",
    "proposed method", "proposed framework", "proposed system",
]


def _research_score(text_lower: str) -> float:
    """Return 0-1 signal for how much the text reads like original research."""
    hits = sum(1 for p in _RESEARCH_PHRASES if p in text_lower)
    return min(1.0, hits / 4.0)


def _strong_method_count(text_lower: str) -> int:
    """Count strict research-specific methodology signals in text."""
    return sum(1 for kw in _STRONG_METHOD_KWS if kw in text_lower)


def is_research_document(text: str, abstract: str) -> tuple[bool, str]:
    """Decide whether the submitted text is a genuine academic research paper.

    Returns (is_research, reason_if_not).

    A real research paper is identified by the presence of standard academic
    sections.  At minimum it needs:
      - An "Abstract" section (or the abstract text was explicitly extracted)
      - An "Introduction" section
      - A methodology / methods section
      - At least one results / findings / discussion section
      OR strong research-phrase evidence supplementing partial structure.
    """
    tl = text.lower()

    # Standard section markers
    has_abstract    = any(m in tl for m in ["abstract", "summary"])
    has_intro       = any(m in tl for m in ["introduction", "1. introduction", "1 introduction"])
    has_method      = any(m in tl for m in [
        "methodology", "methods", "materials and methods",
        "proposed method", "proposed framework", "system design",
        "approach", "implementation",
    ])
    has_results     = any(m in tl for m in [
        "results", "findings", "evaluation", "experiments",
        "discussion", "analysis", "performance",
    ])
    has_conclusion  = any(m in tl for m in ["conclusion", "conclusions", "future work", "summary"])
    has_references  = any(m in tl for m in ["references", "bibliography", "works cited"])

    section_count = sum([has_intro, has_method, has_results, has_conclusion, has_references])

    # Research writing phrases as a secondary signal
    phrase_hits = sum(1 for p in _RESEARCH_PHRASES if p in tl)

    # Strong evidence: abstract + at least 2 supporting sections
    if has_abstract and section_count >= 2:
        return True, ""
    # Supplementary: no explicit abstract but strong research writing + sections
    if phrase_hits >= 2 and section_count >= 3:
        return True, ""
    # Bare minimum: at least 4 sections present (even without explicit abstract label)
    if section_count >= 4:
        return True, ""

    # Build missing-section message for the user
    missing = []
    if not has_abstract:
        missing.append("Abstract")
    if not has_intro:
        missing.append("Introduction")
    if not has_method:
        missing.append("Methodology / Methods")
    if not has_results:
        missing.append("Results / Findings")
    if not has_references:
        missing.append("References")

    reason = (
        "Required research paper sections not found: "
        + ", ".join(missing[:4])
        + ". Please upload a proper academic research paper."
    )
    return False, reason


def is_loaded() -> bool:
    return _MODEL_DATA is not None


def load_model() -> bool:
    """Load trained model from disk. Returns True on success."""
    global _MODEL_DATA
    if _MODEL_DATA is not None:
        return True
    if not _MODEL_PATH.exists():
        logger.warning("[QualityPredictor] Model not found at %s", _MODEL_PATH)
        return False
    try:
        with open(_MODEL_PATH, "rb") as f:
            _MODEL_DATA = pickle.load(f)
        logger.info("[QualityPredictor] Loaded models for targets: %s",
                    _MODEL_DATA.get("target_columns"))
        return True
    except Exception as e:
        logger.error("[QualityPredictor] Failed to load: %s", e)
        return False


def _compute_quality_scores(features: dict, text_lower: str = "") -> dict:
    """Calibrated quality scoring that distinguishes research papers from other docs.

    Key design goals:
    - A real research paper with body citations / technical methodology scores 60-85%.
    - A form, rubric, or generic report scores 20-45% even if it is long or clearly written.
    - Originality is driven by RESEARCH WRITING PHRASES, not text length alone.
    - Methodology uses STRICT research-specific terms, not generic words like
      'analysis', 'approach', 'method' that appear in any document.
    """
    abstract_length  = features["abstract_length"]
    citation_signals = features["citation_signals"]
    avg_sent_len     = features["avg_sentence_length"]
    avg_word_len     = features["avg_word_length"]
    author_count     = features["author_count"]
    word_count       = features["word_count"]

    research_sig  = _research_score(text_lower) if text_lower else 0.0
    strong_method = _strong_method_count(text_lower) if text_lower else 0

    # ── Originality ──────────────────────────────────────────────────────────
    # Research phrases dominate (70%) so that a long form/rubric still scores low.
    # Text length gives a small base (30%) to reward substantial content.
    length_part = min(1.0, abstract_length / 1200.0)
    if abstract_length < 200:
        length_part *= 0.5
    originality = round(min(1.0, length_part * 0.30 + research_sig * 0.70), 4)

    # ── Citation Impact ───────────────────────────────────────────────────────
    # Inline [1]/(Author, Year)/et al. → strongest evidence.
    # For research papers without abstract citations, give partial credit based
    # on research_sig (only real research writing gets this bonus).
    if citation_signals > 0:
        citation_base = min(0.70, citation_signals / 3.0)
    elif word_count > 500 and research_sig >= 0.25:
        # Long research text — body citations very likely
        citation_base = 0.30
    elif research_sig > 0:
        citation_base = 0.15
    else:
        citation_base = 0.05  # Generic doc — almost certainly no real citations

    collab_bonus    = 0.25 if author_count > 1 else 0.0
    citation_impact = round(min(1.0, citation_base + collab_bonus), 4)

    # ── Methodology ───────────────────────────────────────────────────────────
    # Count STRICT research-specific terms only (not 'analysis', 'method', etc.).
    # 3 strong hits → ~75%, 4+ → capped at 1.0.
    methodology = round(min(1.0, strong_method / 4.0), 4)

    # ── Clarity ───────────────────────────────────────────────────────────────
    # Threshold raised to 7.5 (original 6.5 unfairly penalises CS/medical papers).
    clarity_penalty_word = max(0.0, (avg_word_len - 7.5) / 4.0)
    clarity_penalty_sent = max(0.0, (avg_sent_len - 30) / 30.0)
    clarity = round(max(0.30, min(1.0, 1.0 - clarity_penalty_word - clarity_penalty_sent)), 4)

    overall = round(
        originality     * 0.30
        + citation_impact * 0.25
        + methodology   * 0.25
        + clarity       * 0.20,
        4,
    )

    return {
        "originality":     originality,
        "citation_impact": citation_impact,
        "methodology":     methodology,
        "clarity":         clarity,
        "overall":         overall,
    }


def extract_features(title: str, abstract: str, authors: Optional[list] = None,
                      year: Optional[int] = None) -> dict:
    """Extract numerical features from paper text (matches training pipeline)."""
    title = title or ""
    abstract = abstract or ""
    authors = authors or []
    text = f"{title}\n\n{abstract}"

    words = text.split()
    word_count = len(words)
    sentences = max(1, text.count(".") + text.count("!") + text.count("?"))
    avg_word_len = sum(len(w) for w in words) / max(1, word_count)
    avg_sent_len = word_count / sentences

    text_lower = text.lower()
    method_hits = sum(1 for kw in METHODOLOGY_KEYWORDS if kw in text_lower)

    citation_brackets = len(re.findall(r"\[\d+\]", abstract))
    citation_parens = len(re.findall(r"\(\w+,?\s*\d{4}\)", abstract))
    citation_etal = len(re.findall(r"et\s+al\.?", abstract, re.IGNORECASE))
    total_citations = citation_brackets + citation_parens + citation_etal

    try:
        year_int = int(year) if year else 2024
    except (ValueError, TypeError):
        year_int = 2024

    return {
        "word_count": word_count,
        "title_word_count": len(title.split()),
        "sentence_count": sentences,
        "avg_word_length": round(avg_word_len, 2),
        "avg_sentence_length": round(avg_sent_len, 2),
        "methodology_keywords_count": method_hits,
        "author_count": len(authors),
        "citation_signals": total_citations,
        "year": year_int,
        "abstract_length": len(abstract),
        "title_length": len(title),
    }


def predict_quality(title: str, abstract: str, authors: Optional[list] = None,
                     year: Optional[int] = None) -> dict:
    """Predict quality scores for a paper.

    Returns dict with: overall, originality, citation_impact, methodology, clarity,
    plus features used and recommendations.

    The XGBoost models are blended (30 %) with a calibrated heuristic (70 %) to
    prevent systematic 0 % outputs for citation_impact / methodology on technical
    papers that lack inline [1]-style citations or narrow keyword matches.
    """
    title    = title    or ""
    abstract = abstract or ""
    text_lower = f"{title}\n\n{abstract}".lower()

    features = extract_features(title, abstract, authors, year)

    # Calibrated heuristic scores — fair for technical/CS papers
    heuristic = _compute_quality_scores(features, text_lower)

    if load_model():
        feature_cols = _MODEL_DATA["feature_columns"]
        target_cols  = _MODEL_DATA["target_columns"]
        models       = _MODEL_DATA["models"]

        X = np.array([[features[c] for c in feature_cols]])
        blended: dict[str, float] = {}
        for tgt in target_cols:
            model_score = round(max(0.0, min(1.0, float(models[tgt].predict(X)[0]))), 4)
            h_score     = heuristic.get(tgt, model_score)

            # Use dimension-specific blend ratios.
            # methodology and originality are the most biased in the model, so the
            # heuristic overrides them almost entirely.  citation_impact and clarity
            # are more reliable from the model, so it gets a bigger say.
            if tgt == "methodology":
                # Heuristic uses strict research-specific terms → fully authoritative.
                w_model = 0.10
            elif tgt == "originality":
                # Heuristic uses research phrases (not just length) → strongly authoritative.
                w_model = 0.15
            elif tgt == "citation_impact":
                w_model = 0.20
            else:  # clarity
                w_model = 0.40

            blended[tgt] = round(w_model * model_score + (1 - w_model) * h_score, 4)

        # Recompute overall from blended dimensions
        blended["overall"] = round(
            blended["originality"]     * 0.30
            + blended["citation_impact"] * 0.25
            + blended["methodology"]     * 0.25
            + blended["clarity"]         * 0.20,
            4,
        )
        scores  = blended
        version = _MODEL_DATA.get("version", "unknown")
    else:
        scores  = heuristic
        version = "heuristic-only"

    # Generate actionable recommendations
    recommendations = []
    if scores["originality"] < 0.45:
        recommendations.append(
            "Expand the abstract — add problem statement, approach, and key findings "
            "(aim for at least 300 words)"
        )
    if scores["citation_impact"] < 0.40:
        recommendations.append(
            "Add more citations to support claims (e.g., [1], (Author, Year), or 'et al.')"
        )
    if scores["methodology"] < 0.45:
        recommendations.append(
            "Describe methodology more clearly — mention experiment type, dataset, "
            "evaluation method, or model used"
        )
    if scores["clarity"] < 0.50:
        recommendations.append(
            "Improve readability — shorten sentences and simplify overly technical vocabulary"
        )

    return {
        "overall_score":          scores["overall"],
        "originality_score":      scores["originality"],
        "citation_impact_score":  scores["citation_impact"],
        "methodology_score":      scores["methodology"],
        "clarity_score":          scores["clarity"],
        "features":               features,
        "recommendations":        recommendations,
        "model_version":          version,
    }


def _fallback_quality(title: str, abstract: str) -> dict:
    """Used when trained model is unavailable — compute heuristic directly."""
    text_lower = f"{title}\n\n{abstract}".lower()
    features   = extract_features(title, abstract)
    scores     = _compute_quality_scores(features, text_lower)
    return {
        "overall_score":          scores["overall"],
        "originality_score":      scores["originality"],
        "citation_impact_score":  scores["citation_impact"],
        "methodology_score":      scores["methodology"],
        "clarity_score":          scores["clarity"],
        "features":               features,
        "recommendations":        ["Trained model unavailable — using quality heuristic"],
        "model_version":          "heuristic-fallback",
    }


def get_model_info() -> dict:
    """Return model metadata for health endpoint."""
    if not load_model():
        return {"loaded": False, "error": "Model file not found"}
    return {
        "loaded": True,
        "version": _MODEL_DATA.get("version", "unknown"),
        "targets": _MODEL_DATA.get("target_columns", []),
        "metrics": _MODEL_DATA.get("metrics", {}),
    }
