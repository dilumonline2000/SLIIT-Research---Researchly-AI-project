"""IEEE Xplore scraper — uses official API via API key."""

from __future__ import annotations

import logging

from .base_scraper import BaseScraper, Paper


logger = logging.getLogger(__name__)


class IeeeScraper(BaseScraper):
    source_name = "ieee"

    async def scrape(self, query: str, max_results: int | None = None) -> list[Paper]:
        """Query IEEE Xplore API.

        TODO (Phase 2): Call `https://ieeexploreapi.ieee.org/api/v1/search/articles`
        with IEEE_API_KEY, paginate to max_results, map JSON → Paper.
        """
        logger.info("IEEE scrape stub: query=%s", query)
        return []
