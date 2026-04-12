"""Data quality metrics for the scraped corpus."""

from __future__ import annotations

import logging

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger(__name__)


class QualityResponse(BaseModel):
    total_papers: int
    completeness_score: float
    consistency_score: float
    duplicate_rate: float
    sources: dict[str, int]


@router.get("/quality", response_model=QualityResponse)
async def data_quality() -> QualityResponse:
    """Compute completeness + consistency metrics over research_papers.

    1. Count papers and group by source
    2. Check % with abstract, DOI, year (completeness)
    3. Validate field consistency (year range, abstract length)
    4. Estimate duplicate rate
    """
    try:
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "shared"))
        from services.shared.supabase_client import get_supabase_admin
    except ImportError:
        try:
            from shared.supabase_client import get_supabase_admin
        except ImportError:
            return QualityResponse(total_papers=0, completeness_score=0.0, consistency_score=0.0, duplicate_rate=0.0, sources={})

    try:
        sb = get_supabase_admin()
        result = sb.table("research_papers").select("id, title, abstract, doi, publication_year, source").execute()
        papers = result.data or []
    except Exception as e:
        logger.warning("Failed to fetch papers: %s", e)
        papers = []

    if not papers:
        return QualityResponse(total_papers=0, completeness_score=0.0, consistency_score=0.0, duplicate_rate=0.0, sources={})

    total = len(papers)

    # Completeness: % of papers with key fields
    has_abstract = sum(1 for p in papers if p.get("abstract") and len(p["abstract"]) > 50)
    has_doi = sum(1 for p in papers if p.get("doi"))
    has_year = sum(1 for p in papers if p.get("publication_year"))
    has_title = sum(1 for p in papers if p.get("title") and len(p["title"]) > 5)

    completeness = (has_abstract + has_doi + has_year + has_title) / (total * 4) if total else 0.0

    # Consistency: year range check, abstract length sanity
    consistent = 0
    for p in papers:
        year = p.get("publication_year")
        abstract = p.get("abstract") or ""
        if year and 1950 <= year <= 2030 and 50 <= len(abstract) <= 10000:
            consistent += 1
    consistency = consistent / total if total else 0.0

    # Duplicate detection: simple title-based dedup
    titles_lower = [p.get("title", "").lower().strip() for p in papers]
    unique_titles = len(set(titles_lower))
    duplicate_rate = 1.0 - (unique_titles / total) if total else 0.0

    # Source breakdown
    sources: dict[str, int] = {}
    for p in papers:
        src = p.get("source") or "unknown"
        sources[src] = sources.get(src, 0) + 1

    return QualityResponse(
        total_papers=total,
        completeness_score=round(completeness, 4),
        consistency_score=round(consistency, 4),
        duplicate_rate=round(duplicate_rate, 4),
        sources=sources,
    )
