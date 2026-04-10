"""Preprocessing pipeline — clean, normalize, and deduplicate scraped papers.

Usage:
    python scripts/preprocess_data.py --input ml/data/raw --output ml/data/processed

Takes raw JSON files from scrapers and produces cleaned, normalized records
ready for embedding generation and Supabase ingestion.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import unicodedata
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("preprocessor")


def clean_text(text: str | None) -> str:
    """Unicode normalize, collapse whitespace, strip control characters."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)  # control chars
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def clean_title(title: str) -> str:
    """Clean title — collapse whitespace and remove trailing periods."""
    title = clean_text(title)
    title = title.rstrip(".")
    return title


def normalize_doi(doi: str | None) -> str | None:
    """Normalize DOI to lowercase, strip URL prefix."""
    if not doi:
        return None
    doi = doi.strip().lower()
    # Remove common URL prefixes
    for prefix in ["https://doi.org/", "http://doi.org/", "https://dx.doi.org/", "http://dx.doi.org/"]:
        if doi.startswith(prefix):
            doi = doi[len(prefix):]
    return doi if doi else None


def validate_paper(paper: dict) -> bool:
    """Check minimum quality thresholds for a paper record."""
    title = paper.get("title", "")
    abstract = paper.get("abstract", "")

    if not title or len(title) < 10:
        return False
    if not abstract or len(abstract) < 50:
        return False
    # Filter out non-English (rough heuristic: mostly ASCII)
    ascii_ratio = sum(1 for c in abstract if ord(c) < 128) / len(abstract)
    if ascii_ratio < 0.85:
        return False

    return True


def preprocess_paper(paper: dict) -> dict:
    """Clean and normalize a single paper record."""
    return {
        "title": clean_title(paper.get("title", "")),
        "authors": [clean_text(a) for a in paper.get("authors", []) if clean_text(a)],
        "abstract": clean_text(paper.get("abstract", "")),
        "keywords": list(set(
            clean_text(k)
            for k in paper.get("keywords", [])
            if clean_text(k)
        )),
        "doi": normalize_doi(paper.get("doi")),
        "source": paper.get("source", "manual"),
        "publication_year": paper.get("publication_year"),
        "venue": clean_text(paper.get("venue", "")),
        "citation_count": paper.get("citation_count", 0),
        "pdf_url": paper.get("pdf_url"),
    }


def deduplicate_papers(papers: list[dict]) -> list[dict]:
    """Global deduplication across all sources by DOI then by title."""
    seen_dois: set[str] = set()
    seen_titles: set[str] = set()
    unique: list[dict] = []

    for p in papers:
        doi = (p.get("doi") or "").strip().lower()
        title_key = p.get("title", "").strip().lower()

        if doi and doi in seen_dois:
            continue
        if not doi and title_key in seen_titles:
            continue
        if doi:
            seen_dois.add(doi)
        seen_titles.add(title_key)
        unique.append(p)

    return unique


def process_directory(input_dir: Path, output_dir: Path) -> None:
    """Process all raw JSON files from the input directory."""
    output_dir.mkdir(parents=True, exist_ok=True)

    all_papers: list[dict] = []

    # Collect from all raw source directories
    json_files = list(input_dir.rglob("*.json"))
    logger.info("Found %d JSON files in %s", len(json_files), input_dir)

    for json_file in json_files:
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                all_papers.extend(data)
            elif isinstance(data, dict) and "papers" in data:
                all_papers.extend(data["papers"])
        except Exception as e:
            logger.warning("Failed to read %s: %s", json_file, e)

    logger.info("Loaded %d raw papers", len(all_papers))

    # Preprocess
    cleaned = [preprocess_paper(p) for p in all_papers]

    # Validate
    valid = [p for p in cleaned if validate_paper(p)]
    logger.info("After validation: %d papers (dropped %d)", len(valid), len(cleaned) - len(valid))

    # Deduplicate
    unique = deduplicate_papers(valid)
    logger.info("After deduplication: %d papers (dropped %d)", len(unique), len(valid) - len(unique))

    # Save processed output
    output_file = output_dir / "papers_processed.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(unique, f, indent=2, ensure_ascii=False)

    logger.info("Saved %d processed papers to %s", len(unique), output_file)

    # Per-source stats
    source_counts: dict[str, int] = {}
    for p in unique:
        src = p.get("source", "unknown")
        source_counts[src] = source_counts.get(src, 0) + 1
    logger.info("Papers by source: %s", source_counts)


def main() -> None:
    parser = argparse.ArgumentParser(description="Preprocess scraped research papers")
    parser.add_argument("--input", default="ml/data/raw", help="Raw data directory")
    parser.add_argument("--output", default="ml/data/processed", help="Output directory")
    args = parser.parse_args()

    process_directory(Path(args.input), Path(args.output))


if __name__ == "__main__":
    main()
