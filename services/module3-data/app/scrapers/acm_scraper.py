"""ACM Digital Library scraper — Selenium + BeautifulSoup."""

from __future__ import annotations

import logging

from .base_scraper import BaseScraper, Paper


logger = logging.getLogger(__name__)


class AcmScraper(BaseScraper):
    source_name = "acm"

    async def scrape(self, query: str, max_results: int | None = None) -> list[Paper]:
        """Scrape ACM Digital Library via headless Chrome.

        TODO (Phase 2): Use Selenium headless, navigate dl.acm.org/action/doSearch,
        parse result list with BeautifulSoup, extract metadata.
        """
        logger.info("ACM scrape stub: query=%s", query)
        return []
