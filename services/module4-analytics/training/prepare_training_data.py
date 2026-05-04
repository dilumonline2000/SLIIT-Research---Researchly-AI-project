"""
Module 4 Training Data Preparation
====================================

Prepares training data from:
- SLIIT RDA papers (4,219 papers with title, abstract, authors, year, subject)
- Citation NER training data from Module 1
- Document pairs from Module 1 plagiarism

Generates:
- quality_training.json: Per-paper features + computed quality scores (regression target)
- topic_training.json: Title+abstract -> topic label (classification)
- trend_data.json: Year + topic counts for time-series forecasting
"""

import json
import re
import sys
from pathlib import Path
from collections import Counter, defaultdict

# Paths
_SERVICE_ROOT = Path(__file__).parent.parent
_PROJECT_ROOT = _SERVICE_ROOT.parent.parent
_DATA_DIR = _SERVICE_ROOT / "data"
_DATA_DIR.mkdir(exist_ok=True)

SLIIT_PAPERS_PATH = _PROJECT_ROOT / "ml" / "data" / "raw" / "sliit_papers" / "papers_raw_sliit.json"


def safe_load_json(path: Path) -> list:
    """Load JSON file safely with UTF-8 encoding."""
    if not path.exists():
        print(f"[!] File not found: {path}")
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[!] Error loading {path}: {e}")
        return []


def normalize_subject(subject) -> str:
    """Map raw SLIIT subjects to broader topic categories."""
    if not subject:
        return "general"
    # SLIIT subject can be a list of tags - join into one string
    if isinstance(subject, list):
        subject = " ".join(str(s) for s in subject)
    s = str(subject).lower().strip()

    # IT/Computing
    if any(k in s for k in ["computing", "computer", "software", "information technology",
                              "it ", "data science", "machine learning", "ai ", "artificial",
                              "cyber", "networks", "programming", "web", "mobile"]):
        return "computing"
    # Business/Management
    if any(k in s for k in ["business", "management", "marketing", "finance", "accounting",
                              "economics", "hr ", "human resource", "supply chain", "logistics",
                              "leadership", "entrepreneur"]):
        return "business"
    # Engineering
    if any(k in s for k in ["engineering", "civil", "mechanical", "electrical", "electronic",
                              "construction", "architecture"]):
        return "engineering"
    # Health/Bio
    if any(k in s for k in ["health", "medical", "biology", "biotechnology", "nursing",
                              "pharmacy", "nutrition"]):
        return "health"
    # Social Sciences
    if any(k in s for k in ["psychology", "sociology", "education", "law", "political",
                              "social", "media"]):
        return "social_sciences"
    # Sciences
    if any(k in s for k in ["physics", "chemistry", "mathematics", "math ", "statistics"]):
        return "sciences"

    return "general"


METHODOLOGY_KEYWORDS = [
    "experiment", "survey", "case study", "simulation", "prototype",
    "evaluation", "benchmark", "dataset", "statistical", "hypothesis",
    "mixed method", "qualitative", "quantitative", "systematic review",
    "regression", "interview", "questionnaire", "thematic analysis",
    "structural equation", "factor analysis", "anova", "correlation",
    "machine learning", "deep learning", "model", "algorithm",
]

CLARITY_PENALTIES = ["furthermore", "moreover", "however", "therefore",
                       "consequently", "nonetheless", "notwithstanding"]


def extract_quality_features(paper: dict) -> dict:
    """Extract numerical features from a paper for quality scoring."""
    title = paper.get("title", "") or ""
    abstract = paper.get("abstract", "") or ""
    authors = paper.get("authors", []) or []
    year = paper.get("year")
    text = f"{title}\n\n{abstract}"

    # Word/sentence stats
    words = text.split()
    word_count = len(words)
    sentences = max(1, text.count(".") + text.count("!") + text.count("?"))
    avg_word_len = sum(len(w) for w in words) / max(1, word_count)
    avg_sent_len = word_count / sentences

    # Methodology keywords detected
    text_lower = text.lower()
    method_hits = sum(1 for kw in METHODOLOGY_KEYWORDS if kw in text_lower)

    # Author count (collaboration signal)
    author_count = len(authors)

    # Citation indicators in abstract (e.g., "[1]", "(Smith, 2020)", "et al.")
    citation_pattern_brackets = len(re.findall(r"\[\d+\]", abstract))
    citation_pattern_parens = len(re.findall(r"\(\w+,?\s*\d{4}\)", abstract))
    citation_pattern_etal = len(re.findall(r"et\s+al\.?", abstract, re.IGNORECASE))
    total_citation_signals = citation_pattern_brackets + citation_pattern_parens + citation_pattern_etal

    # Title quality
    title_word_count = len(title.split())

    # Year recency (newer = slightly better default signal)
    try:
        year_int = int(year) if year else 2020
    except (ValueError, TypeError):
        year_int = 2020

    return {
        "word_count": word_count,
        "title_word_count": title_word_count,
        "sentence_count": sentences,
        "avg_word_length": round(avg_word_len, 2),
        "avg_sentence_length": round(avg_sent_len, 2),
        "methodology_keywords_count": method_hits,
        "author_count": author_count,
        "citation_signals": total_citation_signals,
        "year": year_int,
        "abstract_length": len(abstract),
        "title_length": len(title),
    }


def compute_quality_score(features: dict, paper: dict) -> dict:
    """Compute heuristic quality score (used as training target).

    This produces ground-truth labels by combining:
    - Originality proxy: text length & uniqueness signals
    - Citation impact: citation pattern density
    - Methodology: methodology keyword count
    - Clarity: readability metrics
    """
    word_count = features["word_count"]
    method_count = features["methodology_keywords_count"]
    citation_signals = features["citation_signals"]
    avg_sent_len = features["avg_sentence_length"]
    avg_word_len = features["avg_word_length"]
    abstract_length = features["abstract_length"]
    author_count = features["author_count"]

    # Originality (0-1): based on abstract length being substantial
    originality = min(1.0, abstract_length / 1500.0)
    if abstract_length < 200:
        originality *= 0.5  # Penalize very short abstracts

    # Citation impact (0-1): citation signal density
    citation_impact = min(1.0, (citation_signals / 5.0) + (0.3 if author_count > 1 else 0.0))

    # Methodology (0-1): keyword detection
    methodology = min(1.0, method_count / 6.0)

    # Clarity (0-1): readability heuristic
    clarity_penalty_sent = max(0, (avg_sent_len - 20) / 30) if avg_sent_len > 20 else 0
    clarity_penalty_word = max(0, (avg_word_len - 6) / 4) if avg_word_len > 6 else 0
    clarity = max(0.3, min(1.0, 1.0 - clarity_penalty_sent - clarity_penalty_word))

    # Weighted overall (matches existing router weights)
    overall = (
        originality * 0.30
        + citation_impact * 0.25
        + methodology * 0.25
        + clarity * 0.20
    )

    return {
        "originality": round(originality, 4),
        "citation_impact": round(citation_impact, 4),
        "methodology": round(methodology, 4),
        "clarity": round(clarity, 4),
        "overall": round(overall, 4),
    }


def build_quality_training_data(papers: list) -> list:
    """Build per-paper feature + label rows for quality model training."""
    rows = []
    for paper in papers:
        if not paper.get("abstract"):
            continue
        features = extract_quality_features(paper)
        scores = compute_quality_score(features, paper)
        rows.append({
            "id": paper.get("id"),
            "title": paper.get("title"),
            "topic": normalize_subject(paper.get("subject", "")),
            "features": features,
            "scores": scores,
        })
    return rows


def build_topic_training_data(papers: list) -> list:
    """Build text -> topic label rows for topic classifier training."""
    rows = []
    for paper in papers:
        title = paper.get("title", "") or ""
        abstract = paper.get("abstract", "") or ""
        if not abstract or len(abstract) < 100:
            continue
        topic = normalize_subject(paper.get("subject", ""))
        if topic == "general":
            continue  # Skip unlabeled
        rows.append({
            "text": f"{title} {abstract}".strip(),
            "label": topic,
        })
    return rows


def build_trend_data(papers: list) -> dict:
    """Build year + topic time series for trend forecasting."""
    counts = defaultdict(lambda: defaultdict(int))
    for paper in papers:
        year = paper.get("year")
        try:
            year_int = int(year) if year else None
        except (ValueError, TypeError):
            year_int = None
        if not year_int or year_int < 2000 or year_int > 2030:
            continue
        topic = normalize_subject(paper.get("subject", ""))
        counts[topic][year_int] += 1
        counts["all"][year_int] += 1

    # Convert to list of {topic, series: [{year, count}]}
    series = {}
    for topic, year_counts in counts.items():
        sorted_years = sorted(year_counts.keys())
        series[topic] = [{"year": y, "count": year_counts[y]} for y in sorted_years]
    return series


def main():
    print("=" * 70)
    print("  MODULE 4 — TRAINING DATA PREPARATION")
    print("=" * 70)

    print(f"\n[1/4] Loading SLIIT papers from {SLIIT_PAPERS_PATH}")
    papers = safe_load_json(SLIIT_PAPERS_PATH)
    print(f"      Loaded {len(papers)} papers")

    if not papers:
        print("[!] No papers found. Exiting.")
        return

    # ── Quality training data ─────────────────────────────────────────
    print("\n[2/4] Building quality training data...")
    quality_data = build_quality_training_data(papers)
    print(f"      Generated {len(quality_data)} quality training rows")

    out_quality = _DATA_DIR / "quality_training.json"
    with open(out_quality, "w", encoding="utf-8") as f:
        json.dump(quality_data, f, indent=2, ensure_ascii=False)
    print(f"      Saved -> {out_quality}")

    # Show distribution of overall scores
    scores = [r["scores"]["overall"] for r in quality_data]
    if scores:
        print(f"      Overall score distribution: min={min(scores):.3f}, "
              f"max={max(scores):.3f}, mean={sum(scores)/len(scores):.3f}")

    # ── Topic training data ───────────────────────────────────────────
    print("\n[3/4] Building topic classification data...")
    topic_data = build_topic_training_data(papers)
    print(f"      Generated {len(topic_data)} topic training rows")

    label_counts = Counter(r["label"] for r in topic_data)
    print(f"      Label distribution:")
    for label, count in label_counts.most_common():
        print(f"        {label:20s}: {count:5d}")

    out_topic = _DATA_DIR / "topic_training.json"
    with open(out_topic, "w", encoding="utf-8") as f:
        json.dump(topic_data, f, indent=2, ensure_ascii=False)
    print(f"      Saved -> {out_topic}")

    # ── Trend data ────────────────────────────────────────────────────
    print("\n[4/4] Building trend forecasting data...")
    trend_data = build_trend_data(papers)
    print(f"      Generated time series for {len(trend_data)} topics")
    for topic, series in trend_data.items():
        if series:
            print(f"        {topic:20s}: {len(series)} years, "
                  f"{series[0]['year']}-{series[-1]['year']}")

    out_trend = _DATA_DIR / "trend_data.json"
    with open(out_trend, "w", encoding="utf-8") as f:
        json.dump(trend_data, f, indent=2, ensure_ascii=False)
    print(f"      Saved -> {out_trend}")

    print("\n" + "=" * 70)
    print("  DATA PREPARATION COMPLETE")
    print("=" * 70)
    print(f"\nNext steps:")
    print(f"  1. Train quality model:   python training/train_quality_model.py")
    print(f"  2. Train topic classifier: python training/train_topic_classifier.py")
    print(f"  3. Train trend forecaster: python training/train_trend_forecaster.py")


if __name__ == "__main__":
    main()
