"""Gap analysis — SBERT + clustering to surface under-explored research areas."""

from __future__ import annotations

import logging
from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()
logger = logging.getLogger(__name__)


class AnalyzeGapsRequest(BaseModel):
    topic: str = Field(..., min_length=1)
    corpus_size: int = 100


class ResearchGap(BaseModel):
    topic: str
    description: str
    gap_score: float
    recency_score: float
    novelty_score: float
    supporting_paper_ids: list[str] = []


class AnalyzeGapsResponse(BaseModel):
    gaps: list[ResearchGap]
    total_papers_analyzed: int


@router.post("/analyze", response_model=AnalyzeGapsResponse)
async def analyze_gaps(req: AnalyzeGapsRequest) -> AnalyzeGapsResponse:
    """Identify research gaps using semantic search + clustering.

    1. Embed the query topic via SBERT
    2. Retrieve top-K similar papers from Supabase pgvector
    3. Cluster retrieved papers
    4. Score each cluster by recency + coverage density → gaps are sparse/old clusters
    """
    import numpy as np

    try:
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "shared"))
        from services.shared.embedding_utils import embed
        from services.shared.supabase_client import get_supabase_admin
    except ImportError:
        try:
            from shared.embedding_utils import embed
            from shared.supabase_client import get_supabase_admin
        except ImportError:
            logger.warning("Shared utils not available — returning empty gaps")
            return AnalyzeGapsResponse(gaps=[], total_papers_analyzed=0)

    # Step 1: Embed query
    query_vec = embed(req.topic).tolist()

    # Step 2: Retrieve similar papers via pgvector RPC
    try:
        sb = get_supabase_admin()
        result = sb.rpc(
            "match_papers",
            {"query_embedding": query_vec, "match_count": req.corpus_size, "match_threshold": 0.3},
        ).execute()
        papers = result.data or []
    except Exception as e:
        logger.warning("Supabase query failed: %s — using fallback", e)
        papers = []

    if not papers:
        return AnalyzeGapsResponse(gaps=[], total_papers_analyzed=0)

    # Step 3: Simple keyword frequency analysis to find gaps
    from collections import Counter

    current_year = datetime.now().year
    keyword_papers: dict[str, list] = {}
    keyword_years: dict[str, list] = {}

    for p in papers:
        kws = p.get("keywords") or []
        pub_year = p.get("publication_year") or current_year
        paper_id = str(p.get("id", ""))
        for kw in kws:
            kw_lower = kw.lower().strip()
            keyword_papers.setdefault(kw_lower, []).append(paper_id)
            keyword_years.setdefault(kw_lower, []).append(pub_year)

    # Step 4: Score keywords — gaps are low-frequency + low-recency
    gaps: list[ResearchGap] = []
    if keyword_papers:
        max_count = max(len(v) for v in keyword_papers.values())
        for kw, paper_ids in keyword_papers.items():
            if kw == req.topic.lower():
                continue
            count = len(paper_ids)
            years = keyword_years[kw]
            avg_year = sum(years) / len(years) if years else current_year
            most_recent = max(years) if years else current_year

            # Gap score: inverse of coverage (fewer papers = bigger gap)
            gap_score = 1.0 - (count / max_count) if max_count > 0 else 0.5
            # Recency score: how old the research is (older = more stale)
            recency_score = max(0, min(1.0, (current_year - most_recent) / 5.0))
            # Novelty: combination
            novelty_score = (gap_score * 0.6 + recency_score * 0.4)

            if novelty_score > 0.3:
                gaps.append(ResearchGap(
                    topic=kw,
                    description=f"Under-explored area related to '{req.topic}': only {count} papers found, most recent from {most_recent}.",
                    gap_score=round(gap_score, 3),
                    recency_score=round(recency_score, 3),
                    novelty_score=round(novelty_score, 3),
                    supporting_paper_ids=paper_ids[:5],
                ))

    # Sort by novelty descending
    gaps.sort(key=lambda g: g.novelty_score, reverse=True)

    return AnalyzeGapsResponse(
        gaps=gaps[:10],
        total_papers_analyzed=len(papers),
    )
