"""Train the plagiarism trend analyzer.

Wraps the trend corpus from `prepare_plagiarism_corpus.py` into a retrieval
index keyed by topic. Each unique topic gets:
  - one SBERT embedding (so the user can query in free text)
  - all (year, stats) records belonging to it

Saved to: models/trained_plagiarism_analyzer/trend_index.pkl
"""

from __future__ import annotations

import argparse
import json
import logging
import pickle
import time
from pathlib import Path
from typing import Any

import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

SERVICE_ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = SERVICE_ROOT.parent.parent
DEFAULT_INPUT = SERVICE_ROOT / "data" / "processed" / "plagiarism_trend_corpus.json"
DEFAULT_OUT_DIR = SERVICE_ROOT / "models" / "trained_plagiarism_analyzer"

MODULE1_SBERT = (PROJECT_ROOT / "services" / "module1-integrity" / "models" / "sbert_plagiarism")
FALLBACK_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def load_sbert():
    from sentence_transformers import SentenceTransformer
    if MODULE1_SBERT.exists() and any(MODULE1_SBERT.iterdir()):
        try:
            return SentenceTransformer(str(MODULE1_SBERT)), "sbert_plagiarism (SLIIT fine-tuned)"
        except Exception as e:
            log.warning("SLIIT SBERT failed (%s) — using base", e)
    return SentenceTransformer(FALLBACK_MODEL), FALLBACK_MODEL


def main() -> None:
    ap = argparse.ArgumentParser(description="Build plagiarism-trend retrieval index.")
    ap.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    ap.add_argument("--version", default="1.0.0")
    args = ap.parse_args()

    if not args.input.exists():
        raise SystemExit(f"Trend corpus not found: {args.input}. Run prepare_plagiarism_corpus.py first.")

    with open(args.input, encoding="utf-8") as f:
        payload = json.load(f)
    records: list[dict[str, Any]] = payload["records"]
    log.info("Loaded %d (topic, year) trend records", len(records))

    # Group by topic so we keep one embedding per topic
    by_topic: dict[str, list[dict[str, Any]]] = {}
    for r in records:
        by_topic.setdefault(r["topic"], []).append(r)

    topics = sorted(by_topic.keys())
    log.info("Encoding %d unique topics", len(topics))

    model, base_name = load_sbert()
    t0 = time.time()
    embs = model.encode(
        topics, batch_size=64, show_progress_bar=True,
        convert_to_numpy=True, normalize_embeddings=True,
    ).astype("float32")
    log.info("Encoded in %.1fs — shape=%s", time.time() - t0, embs.shape)

    # Aggregate per-topic stats across years
    topic_meta: list[dict[str, Any]] = []
    for t in topics:
        rows = sorted(by_topic[t], key=lambda r: r["year"])
        avgs = [r["avg_similarity"] for r in rows]
        max_high = sum(r["n_high_similarity_pairs"] for r in rows)
        latest = rows[-1]
        topic_meta.append({
            "topic": t,
            "n_records": len(rows),
            "n_papers_total": sum(r["n_papers"] for r in rows),
            "avg_similarity_overall": round(float(np.mean(avgs)), 4),
            "max_avg_similarity": round(max(avgs), 4),
            "n_high_similarity_pairs_total": int(max_high),
            "latest_year": latest["year"],
            "latest_trend_direction": latest["trend_direction"],
            "yearly": rows,
        })

    args.out_dir.mkdir(parents=True, exist_ok=True)
    index_path = args.out_dir / "trend_index.pkl"
    with open(index_path, "wb") as f:
        pickle.dump({
            "version": args.version,
            "base_model": base_name,
            "embeddings": embs,
            "topics": topics,
            "topic_meta": topic_meta,
            "embedding_dim": int(embs.shape[1]),
        }, f, protocol=pickle.HIGHEST_PROTOCOL)
    size_mb = index_path.stat().st_size / 1024 / 1024
    log.info("Wrote %s (%.2f MB)", index_path, size_mb)

    metadata = {
        "version": args.version,
        "base_model": base_name,
        "n_topics": len(topics),
        "n_records": len(records),
        "n_papers": payload.get("n_papers"),
        "embedding_dim": int(embs.shape[1]),
        "index_size_mb": round(size_mb, 3),
    }
    with open(args.out_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    log.info("✔ Plagiarism analyzer trained — %d topics indexed.", len(topics))


if __name__ == "__main__":
    main()
