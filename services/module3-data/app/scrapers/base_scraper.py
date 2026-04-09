"""Abstract base scraper — concrete scrapers (IEEE, arXiv, …) inherit from this."""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


logger = logging.getLogger(__name__)


@dataclass
class Paper:
    """Raw scraped paper record — normalized before DB insert."""

    title: str
    authors: list[str] = field(default_factory=list)
    abstract: str | None = None
    keywords: list[str] = field(default_factory=list)
    doi: str | None = None
    source: str = ""
    publication_year: int | None = None
    venue: str | None = None
    citation_count: int = 0
    pdf_url: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)


class BaseScraper(ABC):
    """Abstract scraper interface. Subclasses implement source-specific logic."""

    source_name: str = ""

    def __init__(self, rate_limit: float = 1.0, max_papers: int = 1000) -> None:
        self.rate_limit = rate_limit  # seconds between requests
        self.max_papers = max_papers

    @abstractmethod
    async def scrape(self, query: str, max_results: int | None = None) -> list[Paper]:
        """Scrape papers matching a query."""

    async def scrape_batch(self, queries: list[str]) -> list[Paper]:
        """Scrape multiple queries sequentially, respecting rate limits."""
        all_papers: list[Paper] = []
        for q in queries:
            papers = await self.scrape(q)
            all_papers.extend(papers)
            await asyncio.sleep(self.rate_limit)
        return all_papers

    def deduplicate(self, papers: list[Paper]) -> list[Paper]:
        """Drop duplicates by DOI (preferred) then by title fallback."""
        seen_dois: set[str] = set()
        seen_titles: set[str] = set()
        unique: list[Paper] = []
        for p in papers:
            key_doi = (p.doi or "").strip().lower()
            key_title = p.title.strip().lower()
            if key_doi and key_doi in seen_dois:
                continue
            if not key_doi and key_title in seen_titles:
                continue
            if key_doi:
                seen_dois.add(key_doi)
            seen_titles.add(key_title)
            unique.append(p)
        return unique
