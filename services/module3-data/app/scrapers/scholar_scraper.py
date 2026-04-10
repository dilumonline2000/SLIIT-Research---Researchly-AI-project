"""Google Scholar scraper — uses the `scholarly` library.

Primary use: Enrich supervisor profiles with publication data, h-index,
and research areas. Secondary: scrape papers for training data.

WARNING: Google Scholar aggressively blocks automated access.
Use sparingly and with delays. scholarly handles proxy rotation internally.
"""

from __future__ import annotations

import asyncio
import logging

try:
    from .base_scraper import BaseScraper, Paper
except ImportError:
    from base_scraper import BaseScraper, Paper

logger = logging.getLogger(__name__)


class ScholarScraper(BaseScraper):
    """Scrape Google Scholar via the `scholarly` library.

    This scraper has two modes:
    1. Paper search (for training data)
    2. Author profile lookup (for supervisor enrichment in Module 2)
    """

    source_name = "scholar"

    def __init__(
        self,
        rate_limit: float = 10.0,  # very conservative — Scholar blocks aggressively
        max_papers: int = 500,
    ) -> None:
        super().__init__(rate_limit=rate_limit, max_papers=max_papers)

    def _search_papers_sync(self, query: str, max_results: int) -> list[Paper]:
        """Synchronous paper search via scholarly. Runs in thread executor."""
        from scholarly import scholarly

        papers: list[Paper] = []
        try:
            search_results = scholarly.search_pubs(query)
            count = 0
            for result in search_results:
                if count >= max_results:
                    break

                bib = result.get("bib", {})
                title = bib.get("title", "").strip()
                abstract = bib.get("abstract", "").strip()

                if not title or not abstract or len(abstract) < 50:
                    count += 1
                    continue

                # Parse year
                year_str = bib.get("pub_year", "")
                year = int(year_str) if year_str and year_str.isdigit() else None

                paper = Paper(
                    title=title,
                    authors=bib.get("author", "").split(" and "),
                    abstract=abstract,
                    keywords=[],
                    doi=None,
                    source="scholar",
                    publication_year=year,
                    venue=bib.get("venue", ""),
                    citation_count=result.get("num_citations", 0),
                    pdf_url=result.get("eprint_url"),
                    raw={
                        "scholar_id": result.get("author_pub_id"),
                        "url_scholarbib": result.get("url_scholarbib"),
                    },
                )
                papers.append(paper)
                count += 1

        except Exception as e:
            logger.error("Scholar search failed: %s", e)

        return papers

    async def scrape(self, query: str, max_results: int | None = None) -> list[Paper]:
        """Search Scholar for papers. Runs in thread executor due to sync library."""
        limit = max_results or self.max_papers
        papers = await asyncio.to_thread(self._search_papers_sync, query, limit)
        logger.info("Scholar: scraped %d papers for '%s'", len(papers), query[:50])
        return papers

    async def get_author_profile(self, author_name: str) -> dict | None:
        """Look up an author's profile — used for supervisor enrichment.

        Returns a dict with: name, h_index, citations, research_areas, publications[].
        """
        return await asyncio.to_thread(self._get_author_sync, author_name)

    def _get_author_sync(self, author_name: str) -> dict | None:
        """Synchronous author profile lookup."""
        from scholarly import scholarly

        try:
            search = scholarly.search_author(author_name)
            author = next(search, None)
            if not author:
                logger.warning("Scholar: author '%s' not found", author_name)
                return None

            # Fill in full profile details
            author = scholarly.fill(author, sections=["basics", "indices", "publications"])

            publications = []
            for pub in author.get("publications", [])[:20]:  # limit to 20
                bib = pub.get("bib", {})
                publications.append({
                    "title": bib.get("title", ""),
                    "year": bib.get("pub_year"),
                    "venue": bib.get("venue", ""),
                    "citations": pub.get("num_citations", 0),
                })

            profile = {
                "name": author.get("name", author_name),
                "affiliation": author.get("affiliation", ""),
                "h_index": author.get("hindex", 0),
                "total_citations": author.get("citedby", 0),
                "research_areas": author.get("interests", []),
                "publications": publications,
                "scholar_id": author.get("scholar_id"),
                "url_picture": author.get("url_picture"),
            }

            logger.info(
                "Scholar: found profile for '%s' (h-index: %s, pubs: %d)",
                author_name, profile["h_index"], len(publications),
            )
            return profile

        except StopIteration:
            logger.warning("Scholar: no results for author '%s'", author_name)
            return None
        except Exception as e:
            logger.error("Scholar: author lookup failed for '%s': %s", author_name, e)
            return None

    async def enrich_supervisors(self, supervisor_names: list[str]) -> list[dict]:
        """Look up multiple supervisor profiles sequentially with rate limiting."""
        profiles: list[dict] = []
        for name in supervisor_names:
            profile = await self.get_author_profile(name)
            if profile:
                profiles.append(profile)
            await asyncio.sleep(self.rate_limit)
        return profiles
