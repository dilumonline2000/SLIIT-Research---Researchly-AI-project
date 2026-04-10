"""IEEE Xplore scraper — uses the official IEEE Xplore API.

Requires an API key from https://developer.ieee.org/
Target: 5,000+ papers in CS/IT domains.
Rate limit: ~10 requests/second (generous for authenticated calls).
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

try:
    from .base_scraper import BaseScraper, Paper
except ImportError:
    from base_scraper import BaseScraper, Paper

logger = logging.getLogger(__name__)

IEEE_API_BASE = "https://ieeexploreapi.ieee.org/api/v1/search/articles"


class IeeeScraper(BaseScraper):
    """Scrape papers from IEEE Xplore using the official REST API."""

    source_name = "ieee"

    def __init__(
        self,
        api_key: str,
        rate_limit: float = 1.0,
        max_papers: int = 1000,
    ) -> None:
        super().__init__(rate_limit=rate_limit, max_papers=max_papers)
        self.api_key = api_key

    def _parse_paper(self, article: dict[str, Any]) -> Paper | None:
        """Convert an IEEE API article record into a Paper."""
        title = (article.get("title") or "").strip()
        abstract = (article.get("abstract") or "").strip()

        if not title or not abstract or len(abstract) < 50:
            return None

        # Parse authors from nested structure
        authors_data = article.get("authors", {}).get("authors", [])
        authors = [a.get("full_name", "") for a in authors_data if a.get("full_name")]

        # Parse keywords from multiple keyword types
        keywords: list[str] = []
        for kw_group in article.get("index_terms", {}).values():
            if isinstance(kw_group, dict):
                keywords.extend(kw_group.get("terms", []))

        doi = article.get("doi")
        year_str = article.get("publication_year") or article.get("insert_date", "")[:4]
        year = int(year_str) if year_str and year_str.isdigit() else None

        return Paper(
            title=title,
            authors=authors,
            abstract=abstract,
            keywords=keywords,
            doi=doi,
            source="ieee",
            publication_year=year,
            venue=article.get("publication_title", ""),
            citation_count=article.get("citing_paper_count", 0),
            pdf_url=article.get("pdf_url"),
            raw={
                "article_number": article.get("article_number"),
                "content_type": article.get("content_type"),
                "publisher": article.get("publisher"),
                "is_open_access": article.get("access_type") == "OPEN_ACCESS",
            },
        )

    async def scrape(self, query: str, max_results: int | None = None) -> list[Paper]:
        """Search IEEE Xplore for papers matching a query."""
        limit = max_results or self.max_papers
        papers: list[Paper] = []
        start_record = 1
        page_size = 200  # IEEE max per request

        async with httpx.AsyncClient(timeout=30.0) as client:
            while len(papers) < limit:
                try:
                    resp = await client.get(
                        IEEE_API_BASE,
                        params={
                            "apikey": self.api_key,
                            "querytext": query,
                            "start_record": start_record,
                            "max_records": min(page_size, limit - len(papers)),
                            "sort_field": "article_number",
                            "sort_order": "desc",
                        },
                    )

                    if resp.status_code == 429:
                        logger.warning("IEEE rate limit — sleeping 60s")
                        await asyncio.sleep(60)
                        continue

                    if resp.status_code == 403:
                        logger.error("IEEE API key invalid or expired")
                        break

                    resp.raise_for_status()
                    body = resp.json()

                    articles = body.get("articles", [])
                    if not articles:
                        break

                    for article in articles:
                        paper = self._parse_paper(article)
                        if paper:
                            papers.append(paper)

                    total_records = body.get("total_records", 0)
                    start_record += len(articles)

                    if start_record > total_records:
                        break

                    if len(papers) % 500 == 0 and len(papers) > 0:
                        logger.info("IEEE progress: %d papers", len(papers))

                    await asyncio.sleep(self.rate_limit)

                except httpx.HTTPStatusError as e:
                    logger.error("IEEE API error: %s", e)
                    break
                except httpx.RequestError as e:
                    logger.error("IEEE network error: %s", e)
                    await asyncio.sleep(10)
                    continue

        logger.info("IEEE scrape complete: %d papers for '%s'", len(papers), query[:50])
        return papers

    async def scrape_by_topics(
        self,
        topics: list[str] | None = None,
        max_per_topic: int = 500,
    ) -> list[Paper]:
        """Scrape across multiple CS topics then deduplicate."""
        default_topics = [
            "artificial intelligence",
            "machine learning",
            "deep learning",
            "natural language processing",
            "computer vision",
            "cybersecurity",
            "Internet of Things",
            "cloud computing",
            "software engineering",
            "data mining",
        ]
        topic_list = topics or default_topics
        all_papers: list[Paper] = []

        for topic in topic_list:
            logger.info("IEEE: scraping topic '%s' (max %d)", topic, max_per_topic)
            topic_papers = await self.scrape(topic, max_per_topic)
            all_papers.extend(topic_papers)

        unique = self.deduplicate(all_papers)
        logger.info(
            "IEEE topic scrape: %d → %d after dedup",
            len(all_papers), len(unique),
        )
        return unique
