"""Train the local Gap Analyzer.

The "model" is a retrieval index:
  - Read `data/processed/gap_corpus.json`
  - Embed each gap sentence with the project's SBERT model
    (uses the existing fine-tuned `models/sbert_plagiarism/` if present, else
    falls back to `all-MiniLM-L6-v2`)
  - Save `models/trained_gap_analyzer/gap_index.pkl` containing:
      embeddings : float32 [N, 384]
      records    : list[dict]  (paper_id, title, year, gap_text, gap_type, ...)
      version    : str
      base_model : str
  - Save `models/trained_gap_analyzer/metadata.json` with summary stats.

At inference time the analyzer:
  - encodes a user query (topic / proposal text)
  - cosine-similarity ranks all gaps
  - returns top-K, optionally clustering near-duplicates
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
DEFAULT_INPUT = SERVICE_ROOT / "data" / "processed" / "gap_corpus.json"
DEFAULT_OUT_DIR = SERVICE_ROOT / "models" / "trained_gap_analyzer"

# Use the already-trained SLIIT SBERT if it exists; fall back to base model.
LOCAL_SBERT_DIR = SERVICE_ROOT / "models" / "sbert_plagiarism"
FALLBACK_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def load_sbert():
    """Load SentenceTransformer — prefer the project's fine-tuned model."""
    from sentence_transformers import SentenceTransformer

    if LOCAL_SBERT_DIR.exists() and any(LOCAL_SBERT_DIR.iterdir()):
        log.info("Loading fine-tuned SBERT from %s", LOCAL_SBERT_DIR)
        try:
            return SentenceTransformer(str(LOCAL_SBERT_DIR)), "sbert_plagiarism (SLIIT fine-tuned)"
        except Exception as e:
            log.warning("Fine-tuned SBERT failed (%s) — falling back to %s", e, FALLBACK_MODEL)

    log.info("Loading base SBERT %s", FALLBACK_MODEL)
    return SentenceTransformer(FALLBACK_MODEL), FALLBACK_MODEL


def build_index(records: list[dict[str, Any]], model) -> np.ndarray:
    texts = [r["gap_text"] for r in records]
    log.info("Encoding %d gap sentences (batch=64)…", len(texts))
    t0 = time.time()
    emb = model.encode(
        texts,
        batch_size=64,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    ).astype("float32")
    log.info("Encoded in %.1fs — shape=%s", time.time() - t0, emb.shape)
    return emb


def main() -> None:
    ap = argparse.ArgumentParser(description="Build SBERT retrieval index for research gaps.")
    ap.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    ap.add_argument("--version", default="1.0.0")
    args = ap.parse_args()

    if not args.input.exists():
        raise SystemExit(f"Gap corpus not found at {args.input}. Run prepare_gap_corpus.py first.")

    with open(args.input, encoding="utf-8") as f:
        records: list[dict[str, Any]] = json.load(f)
    log.info("Loaded %d gap records from %s", len(records), args.input)

    model, base_name = load_sbert()
    embeddings = build_index(records, model)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    index_path = args.out_dir / "gap_index.pkl"
    with open(index_path, "wb") as f:
        pickle.dump({
            "embeddings": embeddings,
            "records": records,
            "version": args.version,
            "base_model": base_name,
            "embedding_dim": int(embeddings.shape[1]),
        }, f, protocol=pickle.HIGHEST_PROTOCOL)
    size_mb = index_path.stat().st_size / 1024 / 1024
    log.info("Wrote %s (%.2f MB)", index_path, size_mb)

    type_counts: dict[str, int] = {}
    year_counts: dict[str, int] = {}
    for r in records:
        type_counts[r.get("gap_type", "?")] = type_counts.get(r.get("gap_type", "?"), 0) + 1
        y = str(r.get("year") or "unknown")
        year_counts[y] = year_counts.get(y, 0) + 1

    metadata = {
        "version": args.version,
        "base_model": base_name,
        "n_gaps": len(records),
        "n_papers": len({r.get("paper_id") for r in records if r.get("paper_id")}),
        "embedding_dim": int(embeddings.shape[1]),
        "gap_type_counts": type_counts,
        "year_distribution": dict(sorted(year_counts.items())),
        "index_size_mb": round(size_mb, 3),
    }
    meta_path = args.out_dir / "metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    log.info("Wrote %s", meta_path)
    log.info("✔ Gap analyzer trained — %d gaps from %d unique papers.", metadata["n_gaps"], metadata["n_papers"])


if __name__ == "__main__":
    main()
