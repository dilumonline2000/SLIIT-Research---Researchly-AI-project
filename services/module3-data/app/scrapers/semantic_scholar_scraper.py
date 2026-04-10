"""Semantic Scholar scraper using the free S2 Academic Graph API.

Target: 5,000+ papers with citation metadata and embeddings.
Free tier: 100 requests/5min without a key, higher with API key.
Docs: https://api.semanticscholar.org/api-docs/graph
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

S2_BASE_URL = "https://api.semanticscholar.org/graph/v1"

# Fields to request from the S2 API
PAPER_FIELDS = [
    "paperId",
    "title",
    "abstract",
    "year",
    "venue",
    "citationCount",
    "authors",
    "externalIds",
    "fieldsOfStudy",
    "publicationTypes",
    "journal",
    "openAccessPdf",
    "s2FieldsOfStudy",
]


class SemanticScholarScraper(BaseScraper):
    """Scrape papers from the Semantic Scholar Academic Graph API.

    Uses the bulk search endpoint for efficient retrieval.
    Rate limiting: 100 req / 5 min (free), or higher with API key.
    """

    source_name = "semantic_scholar"

    def __init__(
        self,
        api_key: str | None = None,
        rate_limit: float = 3.5,  # ~100 req / 5 min ≈ 1 per 3s
        max_papers: int = 1000,
    ) -> None:
        super().__init__(rate_limit=rate_limit, max_papers=max_papers)
        self.api_key = api_key
        self._headers: dict[str, str] = {}
        if api_key:
            self._headers["x-api-key"] = api_key

    def _parse_paper(self, data: dict[str, Any]) -> Paper | None:
        """Convert a Semantic Scholar API result into a Paper."""
        title = (data.get("title") or "").strip()
        abstract = (data.get("abstract") or "").strip()

        if not title or not abstract or len(abstract) < 50:
            return None

        authors = [
            a.get("name", "")
            for a in (data.get("authors") or [])
            if a.get("name")
        ]

        # Extract DOI from externalIds
        external_ids = data.get("externalIds") or {}
        doi = external_ids.get("DOI")

        # Build keyword list from S2 fields of study
        keywords = [
            f.get("category", "")
            for f in (data.get("s2FieldsOfStudy") or [])
            if f.get("category")
        ]

        # Open-access PDF URL
        pdf_info = data.get("openAccessPdf") or {}
        pdf_url = pdf_info.get("url")

        journal = data.get("journal") or {}
        venue = data.get("venue") or journal.get("name") or ""

        return Paper(
            title=title,
            authors=authors,
            abstract=abstract,
            keywords=keywords,
            doi=doi,
            source="semantic_scholar",
            publication_year=data.get("year"),
            venue=venue,
            citation_count=data.get("citationCount") or 0,
            pdf_url=pdf_url,
            raw={
                "paperId": data.get("paperId"),
                "externalIds": external_ids,
                "fieldsOfStudy": data.get("fieldsOfStudy"),
                "publicationTypes": data.get("publicationTypes"),
            },
        )

    async def scrape(self, query: str, max_results: int | None = None) -> list[Paper]:
        """Search Semantic Scholar for papers matching a query."""
        limit = max_results or self.max_papers
        papers: list[Paper] = []
        offset = 0
        batch_size = 100  # S2 max per request

        fields_param = ",".join(PAPER_FIELDS)

        async with httpx.AsyncClient(
            base_url=S2_BASE_URL,
            headers=self._headers,
            timeout=30.0,
        ) as client:
            while len(papers) < limit:
                try:
                    resp = await client.get(
                        "/paper/search",
                        params={
                            "query": query,
                            "fields": fields_param,
                            "offset": offset,
                            "limit": min(batch_size, limit - len(papers)),
                        },
                    )

                    if resp.status_code == 429:
                        # Rate limited — back off
                        retry_after = int(resp.headers.get("Retry-After", 60))
                        logger.warning(
                            "S2 rate limit hit. Sleeping %ds", retry_after
                        )
                        await asyncio.sleep(retry_after)
                        continue

                    resp.raise_for_status()
                    body = resp.json()

                    results = body.get("data") or []
                    if not results:
                        logger.info("S2: No more results at offset %d", offset)
                        break

                    for item in results:
                        paper = self._parse_paper(item)
                        if paper:
                            papers.append(paper)

                    total_available = body.get("total", 0)
                    offset += len(results)

                    if offset >= total_available:
                        break

                    if len(papers) % 500 == 0 and len(papers) > 0:
                        logger.info("S2 progress: %d papers collected", len(papers))

                    await asyncio.sleep(self.rate_limit)

                except httpx.HTTPStatusError as e:
                    logger.error("S2 API error: %s %s", e.response.status_code, e.response.text[:200])
                    break
                except httpx.RequestError as e:
                    logger.error("S2 network error: %s", e)
                    await asyncio.sleep(10)
                    continue

        logger.info("S2 scrape complete: %d papers for query '%s'", len(papers), query[:50])
        return papers

    async def scrape_by_topics(
        self,
        topics: list[str] | None = None,
        max_per_topic: int = 500,
    ) -> list[Paper]:
        """Scrape across multiple research topics then deduplicate."""
        default_topics = [
            "artificial intelligence",
            "natural language processing",
            "machine learning",
            "deep learning",
            "computer vision",
            "information retrieval",
            "software engineering",
            "cybersecurity",
            "data science",
            "IoT internet of things",
            "cloud computing",
            "mobile computing",
            "research methodology",
        ]
        topic_list = topics or default_topics
        all_papers: list[Paper] = []

        for topic in topic_list:
            logger.info("S2: scraping topic '%s' (max %d)", topic, max_per_topic)
            topic_papers = await self.scrape(topic, max_per_topic)
            all_papers.extend(topic_papers)
            logger.info(
                "S2: topic '%s' → %d papers (total so far: %d)",
                topic, len(topic_papers), len(all_papers),
            )

        unique = self.deduplicate(all_papers)
        logger.info(
            "S2 topic scrape: %d total → %d after dedup",
            len(all_papers), len(unique),
        )
        return unique

    async def get_paper_by_id(self, paper_id: str) -> Paper | None:
        """Fetch a single paper by Semantic Scholar ID or DOI."""
        fields_param = ",".join(PAPER_FIELDS)
        async with httpx.AsyncClient(
            base_url=S2_BASE_URL,
            headers=self._headers,
            timeout=30.0,
        ) as client:
            resp = await client.get(
                f"/paper/{paper_id}",
                params={"fields": fields_param},
            )
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return self._parse_paper(resp.json())
