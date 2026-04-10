"""Master scraper orchestrator — scrape, preprocess, embed, and ingest.

This is the single entry point for the full Phase 2 data collection pipeline.

Usage:
    # Scrape from all free sources (arXiv + Semantic Scholar)
    python scripts/scrape_research_papers.py --source all

    # Scrape only arXiv, max 500 papers
    python scripts/scrape_research_papers.py --source arxiv --max 500

    # Scrape, skip embedding + Supabase upload (just collect raw data)
    python scripts/scrape_research_papers.py --source arxiv --raw-only

    # Full pipeline: scrape → preprocess → embed → upload to Supabase
    python scripts/scrape_research_papers.py --source all --max 2000 --upload

Requirements:
    pip install arxiv httpx sentence-transformers supabase numpy

Environment variables (for Supabase upload):
    SUPABASE_URL=https://your-project.supabase.co
    SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
from dataclasses import asdict
from pathlib import Path

# Allow imports from services/module3-data (dash in folder name needs importlib)
_services_dir = os.path.join(os.path.dirname(__file__), "..", "services")
_scrapers_dir = os.path.join(_services_dir, "module3-data", "app", "scrapers")
sys.path.insert(0, _scrapers_dir)
sys.path.insert(0, os.path.join(_services_dir, "module3-data"))
sys.path.insert(0, _services_dir)

from base_scraper import Paper
from arxiv_scraper import ArxivScraper
from semantic_scholar_scraper import SemanticScholarScraper

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("orchestrator")

RAW_DATA_DIR = Path("ml/data/raw")
PROCESSED_DIR = Path("ml/data/processed")
EMBEDDINGS_DIR = Path("ml/data/embeddings")


def save_papers_raw(papers: list[Paper], source: str) -> Path:
    """Save scraped papers as raw JSON for the given source."""
    output_dir = RAW_DATA_DIR / source
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "papers.json"
    data = [asdict(p) for p in papers]

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    logger.info("Saved %d raw papers to %s", len(papers), output_file)
    return output_file


async def scrape_arxiv(max_papers: int) -> list[Paper]:
    """Run arXiv scraper across CS categories."""
    scraper = ArxivScraper(max_papers=max_papers)

    # Use category-based scraping for broader coverage
    per_category = max(max_papers // 11, 100)  # 11 categories
    papers = await scraper.scrape_by_categories(max_per_category=per_category)

    # If we got fewer than expected, do a broad query to fill the gap
    if len(papers) < max_papers:
        remaining = max_papers - len(papers)
        logger.info("arXiv: filling gap with broad query (%d more papers)", remaining)
        extra = await scraper.scrape("machine learning OR deep learning OR NLP", remaining)
        papers.extend(extra)
        papers = scraper.deduplicate(papers)

    return papers[:max_papers]


async def scrape_semantic_scholar(max_papers: int) -> list[Paper]:
    """Run Semantic Scholar scraper across research topics."""
    api_key = os.environ.get("SEMANTIC_SCHOLAR_API_KEY")
    scraper = SemanticScholarScraper(api_key=api_key, max_papers=max_papers)

    per_topic = max(max_papers // 13, 100)  # 13 default topics
    papers = await scraper.scrape_by_topics(max_per_topic=per_topic)
    return papers[:max_papers]


async def scrape_ieee(max_papers: int) -> list[Paper]:
    """IEEE Xplore — requires API key. Stub for now."""
    api_key = os.environ.get("IEEE_API_KEY")
    if not api_key:
        logger.warning("IEEE_API_KEY not set — skipping IEEE scraping")
        return []
    logger.warning("IEEE scraper not yet implemented — skipping")
    return []


async def run_scraping(source: str, max_papers: int) -> dict[str, list[Paper]]:
    """Run scraping for the specified source(s)."""
    results: dict[str, list[Paper]] = {}

    if source in ("all", "arxiv"):
        logger.info("=== Starting arXiv scraping (target: %d) ===", max_papers)
        papers = await scrape_arxiv(max_papers)
        results["arxiv"] = papers
        save_papers_raw(papers, "arxiv")

    if source in ("all", "semantic_scholar", "s2"):
        logger.info("=== Starting Semantic Scholar scraping (target: %d) ===", max_papers)
        papers = await scrape_semantic_scholar(max_papers)
        results["semantic_scholar"] = papers
        save_papers_raw(papers, "semantic_scholar")

    if source in ("all", "ieee"):
        papers = await scrape_ieee(max_papers)
        if papers:
            results["ieee"] = papers
            save_papers_raw(papers, "ieee")

    # Summary
    total = sum(len(p) for p in results.values())
    logger.info("=== Scraping complete ===")
    for src, papers in results.items():
        logger.info("  %s: %d papers", src, len(papers))
    logger.info("  TOTAL: %d papers (before cross-source dedup)", total)

    return results


def run_preprocessing() -> Path:
    """Run the preprocessing pipeline on raw data."""
    from preprocess_data import process_directory

    logger.info("=== Running preprocessing ===")
    process_directory(RAW_DATA_DIR, PROCESSED_DIR)
    return PROCESSED_DIR / "papers_processed.json"


def run_embeddings(processed_file: Path, skip_upload: bool) -> None:
    """Generate embeddings and optionally upload to Supabase."""
    from generate_embeddings import load_papers, generate_embeddings_batch, save_embeddings_locally, upsert_to_supabase

    logger.info("=== Generating embeddings ===")
    papers = load_papers(processed_file)
    if not papers:
        logger.error("No papers to embed")
        return

    texts = [f"{p['title']}. {p.get('abstract', '')}" for p in papers]
    embeddings = generate_embeddings_batch(texts, batch_size=64)

    save_embeddings_locally(papers, embeddings, EMBEDDINGS_DIR)

    if not skip_upload:
        supabase_url = os.environ.get("SUPABASE_URL") or os.environ.get("NEXT_PUBLIC_SUPABASE_URL", "")
        supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
        if supabase_url and supabase_key:
            upsert_to_supabase(papers, embeddings, supabase_url, supabase_key)
        else:
            logger.warning(
                "SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY not set — "
                "embeddings saved locally only. Set env vars and rerun with --upload."
            )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Researchly AI — Research Paper Scraping Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--source",
        default="all",
        choices=["all", "arxiv", "semantic_scholar", "s2", "ieee", "acm", "scholar", "sliit"],
        help="Which source to scrape (default: all free sources)",
    )
    parser.add_argument(
        "--max",
        type=int,
        default=1000,
        dest="max_papers",
        help="Max papers per source (default: 1000)",
    )
    parser.add_argument(
        "--raw-only",
        action="store_true",
        help="Only scrape raw data — skip preprocessing and embeddings",
    )
    parser.add_argument(
        "--upload",
        action="store_true",
        help="Upload embeddings to Supabase (requires env vars)",
    )
    args = parser.parse_args()

    # Step 1: Scrape
    results = asyncio.run(run_scraping(args.source, args.max_papers))

    if args.raw_only:
        logger.info("Raw-only mode — stopping after scraping")
        return

    if not any(results.values()):
        logger.error("No papers scraped — nothing to preprocess")
        return

    # Step 2: Preprocess
    processed_file = run_preprocessing()

    # Step 3: Embed + Upload
    skip_upload = not args.upload
    run_embeddings(processed_file, skip_upload=skip_upload)

    logger.info("=== Pipeline complete ===")


if __name__ == "__main__":
    main()
