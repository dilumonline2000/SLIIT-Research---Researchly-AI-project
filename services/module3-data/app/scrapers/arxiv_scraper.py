"""arXiv scraper using the official `arxiv` Python client."""

from __future__ import annotations

import asyncio
import logging

from .base_scraper import BaseScraper, Paper


logger = logging.getLogger(__name__)


class ArxivScraper(BaseScraper):
    source_name = "arxiv"

    async def scrape(self, query: str, max_results: int | None = None) -> list[Paper]:
        """Query arXiv and convert results to Paper records.

        TODO (Phase 2): Implement with `arxiv.Search(query=..., max_results=...)`.
        The arxiv library is synchronous — run in a thread executor.
        """
        limit = max_results or self.max_papers
        logger.info("arXiv scrape stub: query=%s max=%s", query, limit)
        # Placeholder — return empty list until Phase 2.
        await asyncio.sleep(0)
        return []
