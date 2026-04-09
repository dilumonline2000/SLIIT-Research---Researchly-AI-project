"""Master scraper orchestrator — runs all 6 sources and ingests into Supabase.

Usage:
    python scripts/scrape_research_papers.py --source all
    python scripts/scrape_research_papers.py --source arxiv --max 5000

TODO (Phase 2): Wire up actual scrapers, deduplicate, generate SBERT embeddings,
bulk-insert into public.research_papers.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys

# Make services/ importable
sys.path.insert(0, "services")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("scrape-orchestrator")


async def run_all(max_papers: int) -> None:
    """Run every scraper in parallel up to max_papers each."""
    logger.warning(
        "Scraper orchestrator is a scaffold — implement in Phase 2. "
        "Will run: IEEE, arXiv, ACM, SLIIT, Google Scholar, Semantic Scholar."
    )
    await asyncio.sleep(0)


async def run_source(source: str, max_papers: int) -> None:
    logger.warning("Scraper for %s is a stub — implement in Phase 2.", source)
    await asyncio.sleep(0)


def main() -> None:
    parser = argparse.ArgumentParser(description="Researchly paper scraping orchestrator")
    parser.add_argument(
        "--source",
        default="all",
        choices=["all", "ieee", "arxiv", "acm", "sliit", "scholar", "semantic_scholar"],
    )
    parser.add_argument("--max", type=int, default=1000, dest="max_papers")
    args = parser.parse_args()

    if args.source == "all":
        asyncio.run(run_all(args.max_papers))
    else:
        asyncio.run(run_source(args.source, args.max_papers))


if __name__ == "__main__":
    main()
