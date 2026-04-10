"""Generate SBERT embeddings for processed papers and store in Supabase pgvector.

Usage:
    python scripts/generate_embeddings.py --input ml/data/processed/papers_processed.json

This script:
1. Loads preprocessed papers from JSON
2. Generates 768-dim SBERT embeddings for each abstract
3. Upserts papers + embeddings into public.research_papers in Supabase
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path

import numpy as np

# Allow imports from services/shared
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "services"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("embeddings")


def load_papers(path: Path) -> list[dict]:
    """Load preprocessed papers from JSON."""
    with open(path, "r", encoding="utf-8") as f:
        papers = json.load(f)
    logger.info("Loaded %d papers from %s", len(papers), path)
    return papers


def generate_embeddings_batch(
    texts: list[str],
    batch_size: int = 64,
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
) -> np.ndarray:
    """Generate SBERT embeddings for a list of texts."""
    from sentence_transformers import SentenceTransformer

    logger.info(
        "Loading SBERT model '%s' and encoding %d texts",
        model_name,
        len(texts),
    )
    model = SentenceTransformer(model_name)
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=True,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )
    logger.info("Generated embeddings: shape=%s", embeddings.shape)
    return embeddings.astype(np.float32)


def upsert_to_supabase(
    papers: list[dict],
    embeddings: np.ndarray,
    supabase_url: str,
    supabase_key: str,
    batch_size: int = 100,
) -> None:
    """Upsert papers with embeddings into Supabase research_papers table."""
    from supabase import create_client

    client = create_client(supabase_url, supabase_key)

    total = len(papers)
    inserted = 0
    errors = 0

    for i in range(0, total, batch_size):
        batch_papers = papers[i : i + batch_size]
        batch_embeddings = embeddings[i : i + batch_size]

        rows = []
        for paper, embedding in zip(batch_papers, batch_embeddings):
            row = {
                "title": paper["title"],
                "authors": paper.get("authors", []),
                "abstract": paper.get("abstract", ""),
                "keywords": paper.get("keywords", []),
                "doi": paper.get("doi"),
                "source": paper.get("source", "manual"),
                "publication_year": paper.get("publication_year"),
                "venue": paper.get("venue", ""),
                "citation_count": paper.get("citation_count", 0),
                "pdf_url": paper.get("pdf_url"),
                "topic_labels": paper.get("keywords", []),
                "embedding": embedding.tolist(),
            }
            rows.append(row)

        try:
            # Upsert by DOI (if available) to avoid duplicates
            result = (
                client.table("research_papers")
                .upsert(rows, on_conflict="doi")
                .execute()
            )
            inserted += len(rows)
            logger.info(
                "Upserted batch %d-%d / %d (%d total inserted)",
                i, i + len(rows), total, inserted,
            )
        except Exception as e:
            errors += len(rows)
            logger.error("Failed to upsert batch %d-%d: %s", i, i + len(rows), e)
            # Try individual inserts for this batch as fallback
            for row in rows:
                try:
                    client.table("research_papers").insert(row).execute()
                    inserted += 1
                    errors -= 1
                except Exception as inner_e:
                    logger.warning(
                        "Individual insert failed for '%s': %s",
                        row["title"][:50],
                        inner_e,
                    )

    logger.info(
        "Supabase ingestion complete: %d inserted, %d errors out of %d total",
        inserted, errors, total,
    )


def save_embeddings_locally(
    papers: list[dict],
    embeddings: np.ndarray,
    output_dir: Path,
) -> None:
    """Save embeddings locally as .npy for backup / offline use."""
    output_dir.mkdir(parents=True, exist_ok=True)

    np.save(output_dir / "embeddings.npy", embeddings)

    # Save paper IDs/titles for alignment
    metadata = [
        {"index": i, "title": p["title"], "doi": p.get("doi"), "source": p.get("source")}
        for i, p in enumerate(papers)
    ]
    with open(output_dir / "embedding_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    logger.info(
        "Saved embeddings (%s) and metadata to %s",
        embeddings.shape,
        output_dir,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate SBERT embeddings and store in Supabase")
    parser.add_argument(
        "--input",
        default="ml/data/processed/papers_processed.json",
        help="Path to preprocessed papers JSON",
    )
    parser.add_argument(
        "--model",
        default="sentence-transformers/all-MiniLM-L6-v2",
        help="SBERT model name",
    )
    parser.add_argument("--batch-size", type=int, default=64, help="Encoding batch size")
    parser.add_argument(
        "--save-local",
        default="ml/data/embeddings",
        help="Directory to save embeddings locally (set to empty to skip)",
    )
    parser.add_argument(
        "--skip-supabase",
        action="store_true",
        help="Skip Supabase upload (just generate + save locally)",
    )
    args = parser.parse_args()

    # Load papers
    papers = load_papers(Path(args.input))
    if not papers:
        logger.error("No papers to process")
        return

    # Build texts for embedding (title + abstract for richer representation)
    texts = [
        f"{p['title']}. {p.get('abstract', '')}"
        for p in papers
    ]

    # Generate embeddings
    embeddings = generate_embeddings_batch(
        texts,
        batch_size=args.batch_size,
        model_name=args.model,
    )

    # Save locally (backup)
    if args.save_local:
        save_embeddings_locally(papers, embeddings, Path(args.save_local))

    # Upload to Supabase
    if not args.skip_supabase:
        supabase_url = os.environ.get("SUPABASE_URL") or os.environ.get("NEXT_PUBLIC_SUPABASE_URL", "")
        supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

        if not supabase_url or not supabase_key:
            logger.error(
                "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set. "
                "Use --skip-supabase to only generate embeddings locally."
            )
            return

        upsert_to_supabase(papers, embeddings, supabase_url, supabase_key)
    else:
        logger.info("Skipped Supabase upload (--skip-supabase)")


if __name__ == "__main__":
    main()
