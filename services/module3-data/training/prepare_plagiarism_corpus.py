"""Build the plagiarism-trend corpus from SLIIT papers.

For every (subject_topic, year) bucket we compute:
  - n_papers
  - mean / median / max pairwise SBERT similarity within the bucket
  - 95th-percentile similarity (catches near-duplicates)
  - trend_direction relative to previous year (increasing/decreasing/stable)
  - representative paper pairs (top-K most similar pairs in the bucket)

This gives us a *retrievable* trend corpus: at runtime the user types a topic
or category, we find the most similar topic-bucket(s) by SBERT, and return
their precomputed plagiarism statistics + sample evidence pairs.

Reads:
  ml/data/raw/sliit_papers/papers_raw_sliit.json
Writes:
  data/processed/plagiarism_trend_corpus.json

Heavy step (encodes 4,200 abstracts) — ~90 s on CPU.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
from collections import defaultdict
from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

SERVICE_ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = SERVICE_ROOT.parent.parent

DEFAULT_INPUT = PROJECT_ROOT / "ml" / "data" / "raw" / "sliit_papers" / "papers_raw_sliit.json"
DEFAULT_OUTPUT = SERVICE_ROOT / "data" / "processed" / "plagiarism_trend_corpus.json"

# Reuse the SLIIT-trained SBERT from module 1 if present
MODULE1_SBERT = (PROJECT_ROOT / "services" / "module1-integrity" / "models" / "sbert_plagiarism")
FALLBACK_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

MIN_BUCKET_SIZE = 3       # need at least 3 papers to compute pairwise stats
TOP_PAIRS_PER_BUCKET = 5  # representative pairs to keep
SIM_FLAG_THRESHOLD = 0.80 # pairs above this get flagged as "high similarity"
TOPIC_TRUNCATE = 60


_split_re = re.compile(r"[;,·|]+")
_clean_re = re.compile(r"[^a-z0-9 \-]+")


def _normalize_topic(raw: Any) -> str:
    if isinstance(raw, list):
        items = []
        for x in raw:
            items.extend(_split_re.split(str(x)))
        # use the most-specific (= longest non-trivial) token
        items = [s for s in items if s.strip()]
        if not items:
            return ""
        items.sort(key=len, reverse=True)
        candidate = items[0]
    else:
        candidate = str(raw or "").split(_split_re.pattern)[0]
        candidate = _split_re.split(str(raw or ""))[0] if raw else ""
    s = candidate.strip().lower()
    s = _clean_re.sub(" ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s[:TOPIC_TRUNCATE]


def load_sbert():
    from sentence_transformers import SentenceTransformer
    _has_weights = (MODULE1_SBERT / "model.safetensors").exists() or (MODULE1_SBERT / "pytorch_model.bin").exists()
    if MODULE1_SBERT.exists() and _has_weights:
        log.info("Loading SLIIT-tuned SBERT from %s", MODULE1_SBERT)
        try:
            return SentenceTransformer(str(MODULE1_SBERT)), "sbert_plagiarism (SLIIT fine-tuned)"
        except Exception as e:
            log.warning("SLIIT SBERT failed (%s) — using base", e)
    return SentenceTransformer(FALLBACK_MODEL), FALLBACK_MODEL


def _direction(curr: float, prev: float | None) -> str:
    if prev is None:
        return "baseline"
    if curr > prev + 0.02:
        return "increasing"
    if curr < prev - 0.02:
        return "decreasing"
    return "stable"


def main() -> None:
    ap = argparse.ArgumentParser(description="Compute SLIIT plagiarism-trend corpus.")
    ap.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    ap.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = ap.parse_args()

    with open(args.input, encoding="utf-8") as f:
        papers = json.load(f)
    log.info("Loaded %d papers", len(papers))

    # Pre-filter to papers with usable abstract + topic + year
    rows: list[dict[str, Any]] = []
    for p in papers:
        abstract = (p.get("abstract") or "").strip()
        if len(abstract) < 120:
            continue
        topic = _normalize_topic(p.get("subject"))
        if not topic:
            continue
        try:
            year = int(p.get("year"))
        except (TypeError, ValueError):
            continue
        rows.append({
            "paper_id": str(p.get("id") or p.get("handle") or ""),
            "title": (p.get("title") or "").strip(),
            "year": year,
            "topic": topic,
            "url": p.get("url") or p.get("source_url") or "",
            "abstract": abstract,
        })
    log.info("Kept %d papers with topic + year + abstract", len(rows))

    # Group by topic
    by_topic: dict[str, list[int]] = defaultdict(list)
    for i, r in enumerate(rows):
        by_topic[r["topic"]].append(i)
    big_topics = {t: idxs for t, idxs in by_topic.items() if len(idxs) >= MIN_BUCKET_SIZE}
    log.info("Topics with >= %d papers: %d / %d total", MIN_BUCKET_SIZE, len(big_topics), len(by_topic))

    # Encode all abstracts
    model, base_name = load_sbert()
    abstracts = [r["abstract"] for r in rows]
    log.info("Encoding %d abstracts…", len(abstracts))
    embs = model.encode(
        abstracts, batch_size=64, show_progress_bar=True,
        convert_to_numpy=True, normalize_embeddings=True,
    ).astype("float32")
    log.info("Embeddings shape=%s", embs.shape)

    trend_records: list[dict[str, Any]] = []

    for topic, idxs in big_topics.items():
        # Bucket by year within the topic
        per_year: dict[int, list[int]] = defaultdict(list)
        for i in idxs:
            per_year[rows[i]["year"]].append(i)

        prev_avg: float | None = None
        for year in sorted(per_year.keys()):
            year_idxs = per_year[year]
            if len(year_idxs) < MIN_BUCKET_SIZE:
                continue
            # All pairwise sims (could be slow for very big buckets; cap at 60)
            cap_idxs = year_idxs[:60]
            v = embs[cap_idxs]
            sims = v @ v.T
            tri_i, tri_j = np.triu_indices(len(cap_idxs), k=1)
            pair_sims = sims[tri_i, tri_j]
            if pair_sims.size == 0:
                continue
            avg_sim = float(pair_sims.mean())
            max_sim = float(pair_sims.max())
            p95 = float(np.percentile(pair_sims, 95))
            n_high = int((pair_sims >= SIM_FLAG_THRESHOLD).sum())

            # Top representative pairs
            pair_scores = list(zip(pair_sims.tolist(), tri_i.tolist(), tri_j.tolist()))
            pair_scores.sort(key=lambda x: x[0], reverse=True)
            top_pairs = []
            for sim, ai, bi in pair_scores[:TOP_PAIRS_PER_BUCKET]:
                a = rows[cap_idxs[ai]]
                b = rows[cap_idxs[bi]]
                top_pairs.append({
                    "similarity": round(sim, 4),
                    "paper_a": {"paper_id": a["paper_id"], "title": a["title"], "url": a["url"]},
                    "paper_b": {"paper_id": b["paper_id"], "title": b["title"], "url": b["url"]},
                })

            direction = _direction(avg_sim, prev_avg)
            prev_avg = avg_sim

            trend_records.append({
                "topic": topic,
                "year": year,
                "n_papers": len(year_idxs),
                "avg_similarity": round(avg_sim, 4),
                "max_similarity": round(max_sim, 4),
                "p95_similarity": round(p95, 4),
                "n_high_similarity_pairs": n_high,
                "trend_direction": direction,
                "top_pairs": top_pairs,
            })

    log.info("Computed %d (topic, year) trend rows", len(trend_records))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": "1.0.0",
        "base_model": base_name,
        "n_papers": len(rows),
        "n_topics": len(big_topics),
        "n_records": len(trend_records),
        "records": trend_records,
    }
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    log.info("Wrote %s (%.1f KB)", args.output, args.output.stat().st_size / 1024)


if __name__ == "__main__":
    main()
