"""Google Scholar scraper — uses the `scholarly` library for supervisor profiles."""

from __future__ import annotations

import logging

from .base_scraper import BaseScraper, Paper


logger = logging.getLogger(__name__)


class ScholarScraper(BaseScraper):
    source_name = "scholar"

    async def scrape(self, query: str, max_results: int | None = None) -> list[Paper]:
        """Query Google Scholar via `scholarly`.

        TODO (Phase 2): Use scholarly.search_pubs() for query scraping OR
        scholarly.search_author() for supervisor profile enrichment.
        Rate limit aggressively — Scholar blocks abusive clients.
        """
        logger.info("Scholar scrape stub: query=%s", query)
        return []
