"""SLIIT institutional repository scraper."""

from __future__ import annotations

import logging

from .base_scraper import BaseScraper, Paper


logger = logging.getLogger(__name__)


class SliitScraper(BaseScraper):
    source_name = "sliit"

    async def scrape(self, query: str, max_results: int | None = None) -> list[Paper]:
        """Scrape SLIIT digital library (digital.lib.sliit.lk).

        TODO (Phase 2): Use requests + BeautifulSoup, iterate result pages,
        extract thesis/proposal metadata including supervisor/department.
        """
        logger.info("SLIIT scrape stub: query=%s", query)
        return []
