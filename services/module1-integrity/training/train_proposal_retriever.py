"""Train the local Proposal Retriever.

Builds a SBERT retrieval index over the proposal corpus. Each entry is a SLIIT
paper turned into a "proposal exemplar" (problem, objectives-hint, methodology-hint).

At inference time:
  - encode the user's topic
  - cosine-rank exemplars
  - assemble a new proposal by stitching templates from top-K matches

Saves:
  models/trained_proposal_retriever/proposal_index.pkl
  models/trained_proposal_retriever/metadata.json
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
DEFAULT_INPUT = SERVICE_ROOT / "data" / "processed" / "proposal_corpus.json"
DEFAULT_OUT_DIR = SERVICE_ROOT / "models" / "trained_proposal_retriever"

LOCAL_SBERT_DIR = SERVICE_ROOT / "models" / "sbert_plagiarism"
FALLBACK_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def load_sbert():
    from sentence_transformers import SentenceTransformer

    if LOCAL_SBERT_DIR.exists() and any(LOCAL_SBERT_DIR.iterdir()):
        log.info("Loading fine-tuned SBERT from %s", LOCAL_SBERT_DIR)
        try:
            return SentenceTransformer(str(LOCAL_SBERT_DIR)), "sbert_plagiarism (SLIIT fine-tuned)"
        except Exception as e:
            log.warning("Fine-tuned SBERT failed (%s) — falling back to %s", e, FALLBACK_MODEL)
    log.info("Loading base SBERT %s", FALLBACK_MODEL)
    return SentenceTransformer(FALLBACK_MODEL), FALLBACK_MODEL


def make_embedding_text(rec: dict[str, Any]) -> str:
    """Stitched representation used for the embedding (title + subject + abstract).
    Title and subject are weighted heavily by appearing first."""
    parts = [rec.get("title", "")]
    subj = rec.get("subject")
    if isinstance(subj, list):
        subj = ", ".join(s for s in subj if s)
    if subj:
        parts.append(str(subj))
    abstract = rec.get("abstract", "")
    parts.append(abstract[:500])
    return ". ".join(p for p in parts if p)


def main() -> None:
    ap = argparse.ArgumentParser(description="Build SBERT retrieval index for proposal exemplars.")
    ap.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    ap.add_argument("--version", default="1.0.0")
    args = ap.parse_args()

    if not args.input.exists():
        raise SystemExit(f"Proposal corpus not found at {args.input}. Run prepare_proposal_corpus.py first.")

    with open(args.input, encoding="utf-8") as f:
        records: list[dict[str, Any]] = json.load(f)
    log.info("Loaded %d proposal exemplars from %s", len(records), args.input)

    model, base_name = load_sbert()
    texts = [make_embedding_text(r) for r in records]

    log.info("Encoding %d proposal texts (batch=64)…", len(texts))
    t0 = time.time()
    embeddings = model.encode(
        texts,
        batch_size=64,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    ).astype("float32")
    log.info("Encoded in %.1fs — shape=%s", time.time() - t0, embeddings.shape)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    index_path = args.out_dir / "proposal_index.pkl"
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

    year_counts: dict[str, int] = {}
    for r in records:
        y = str(r.get("year") or "unknown")
        year_counts[y] = year_counts.get(y, 0) + 1

    metadata = {
        "version": args.version,
        "base_model": base_name,
        "n_exemplars": len(records),
        "embedding_dim": int(embeddings.shape[1]),
        "year_distribution": dict(sorted(year_counts.items())),
        "index_size_mb": round(size_mb, 3),
    }
    with open(args.out_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    log.info("✔ Proposal retriever trained — %d exemplars indexed.", metadata["n_exemplars"])


if __name__ == "__main__":
    main()
