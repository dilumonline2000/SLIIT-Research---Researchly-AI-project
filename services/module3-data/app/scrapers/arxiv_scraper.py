"""arXiv scraper using the official `arxiv` Python client.

Target: 10,000+ papers from CS categories (cs.AI, cs.CL, cs.IR, cs.LG, cs.SE).
The arXiv API is free, no key needed, but has a 3-second rate limit recommendation.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime

import arxiv

try:
    from .base_scraper import BaseScraper, Paper
except ImportError:
    from base_scraper import BaseScraper, Paper

logger = logging.getLogger(__name__)

# CS categories relevant to the platform's research domains
DEFAULT_CATEGORIES = [
    "cs.AI",   # Artificial Intelligence
    "cs.CL",   # Computation and Language (NLP)
    "cs.IR",   # Information Retrieval
    "cs.LG",   # Machine Learning
    "cs.SE",   # Software Engineering
    "cs.CV",   # Computer Vision
    "cs.CR",   # Cryptography and Security
    "cs.DB",   # Databases
    "cs.DC",   # Distributed Computing
    "cs.NI",   # Networking
    "cs.HC",   # Human-Computer Interaction
]


class ArxivScraper(BaseScraper):
    """Scrape papers from arXiv using the official API client.

    The arxiv library handles pagination internally. We run it in a thread
    executor since it's synchronous and involves network I/O.
    """

    source_name = "arxiv"

    def __init__(
        self,
        rate_limit: float = 3.0,  # arXiv recommends >= 3s between requests
        max_papers: int = 1000,
        sort_by: arxiv.SortCriterion = arxiv.SortCriterion.SubmittedDate,
    ) -> None:
        super().__init__(rate_limit=rate_limit, max_papers=max_papers)
        self.sort_by = sort_by

    def _build_query(self, query: str, categories: list[str] | None = None) -> str:
        """Build an arXiv API query string with optional category filter."""
        cats = categories or DEFAULT_CATEGORIES
        cat_filter = " OR ".join(f"cat:{c}" for c in cats)

        if query.strip():
            return f"({query}) AND ({cat_filter})"
        return f"({cat_filter})"

    def _result_to_paper(self, result: arxiv.Result) -> Paper:
        """Convert an arxiv.Result into our Paper dataclass."""
        # Extract year from published date
        pub_date: datetime = result.published
        year = pub_date.year if pub_date else None

        # Extract primary category and all categories
        categories = [c for c in (result.categories or [])]

        return Paper(
            title=result.title.strip().replace("\n", " "),
            authors=[a.name for a in (result.authors or [])],
            abstract=(result.summary or "").strip().replace("\n", " "),
            keywords=categories,
            doi=result.doi,
            source="arxiv",
            publication_year=year,
            venue=result.journal_ref or f"arXiv:{result.entry_id.split('/')[-1]}",
            citation_count=0,  # arXiv doesn't provide citation counts
            pdf_url=result.pdf_url,
            raw={
                "arxiv_id": result.entry_id,
                "primary_category": result.primary_category,
                "updated": result.updated.isoformat() if result.updated else None,
                "published": pub_date.isoformat() if pub_date else None,
                "comment": result.comment,
                "links": [str(l) for l in (result.links or [])],
            },
        )

    def _scrape_sync(self, query: str, max_results: int) -> list[Paper]:
        """Synchronous arXiv fetch — called via asyncio.to_thread."""
        full_query = self._build_query(query)
        logger.info(
            "arXiv scraping: query='%s' max_results=%d sort=%s",
            full_query[:100],
            max_results,
            self.sort_by.value,
        )

        search = arxiv.Search(
            query=full_query,
            max_results=max_results,
            sort_by=self.sort_by,
            sort_order=arxiv.SortOrder.Descending,
        )

        client = arxiv.Client(
            page_size=100,              # fetch 100 results per API call
            delay_seconds=self.rate_limit,
            num_retries=3,
        )

        papers: list[Paper] = []
        count = 0
        for result in client.results(search):
            try:
                paper = self._result_to_paper(result)
                # Skip papers without abstracts (not useful for embeddings)
                if not paper.abstract or len(paper.abstract) < 50:
                    continue
                papers.append(paper)
                count += 1
                if count % 500 == 0:
                    logger.info("arXiv progress: %d papers collected", count)
            except Exception as e:
                logger.warning("Failed to parse arXiv result: %s", e)
                continue

        logger.info("arXiv scrape complete: %d papers collected", len(papers))
        return papers

    async def scrape(self, query: str, max_results: int | None = None) -> list[Paper]:
        """Async wrapper — runs the synchronous arXiv client in a thread."""
        limit = max_results or self.max_papers
        papers = await asyncio.to_thread(self._scrape_sync, query, limit)
        return papers

    async def scrape_by_categories(
        self,
        categories: list[str] | None = None,
        max_per_category: int = 1000,
    ) -> list[Paper]:
        """Scrape papers from each category individually then deduplicate.

        This approach gets broader coverage than a single query.
        """
        cats = categories or DEFAULT_CATEGORIES
        all_papers: list[Paper] = []

        for cat in cats:
            logger.info("Scraping arXiv category: %s (max %d)", cat, max_per_category)
            search = arxiv.Search(
                query=f"cat:{cat}",
                max_results=max_per_category,
                sort_by=self.sort_by,
                sort_order=arxiv.SortOrder.Descending,
            )
            category_papers = await asyncio.to_thread(
                self._fetch_category, search
            )
            all_papers.extend(category_papers)
            logger.info(
                "Category %s: got %d papers (total so far: %d)",
                cat, len(category_papers), len(all_papers),
            )
            await asyncio.sleep(self.rate_limit)

        unique = self.deduplicate(all_papers)
        logger.info(
            "arXiv category scrape: %d total → %d after dedup",
            len(all_papers), len(unique),
        )
        return unique

    def _fetch_category(self, search: arxiv.Search) -> list[Paper]:
        """Fetch all results for a single arxiv.Search object."""
        client = arxiv.Client(
            page_size=100,
            delay_seconds=self.rate_limit,
            num_retries=3,
        )
        papers: list[Paper] = []
        for result in client.results(search):
            try:
                paper = self._result_to_paper(result)
                if paper.abstract and len(paper.abstract) >= 50:
                    papers.append(paper)
            except Exception as e:
                logger.warning("Failed to parse arXiv result: %s", e)
        return papers
