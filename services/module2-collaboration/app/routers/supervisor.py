"""Supervisor matching endpoint — fine-tuned SBERT + multi-factor scoring."""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.supervisor_matcher import match_supervisors as find_supervisors

router = APIRouter()
logger = logging.getLogger(__name__)


class MatchSupervisorsRequest(BaseModel):
    """Request to find matching supervisors for a student proposal.

    Can accept either:
    - A free-text `proposal` string (new way — uses fine-tuned SBERT)
    - Legacy format: `research_interests[]` + `abstract` (converted to proposal string)
    """

    proposal: str | None = None  # Free-text research proposal (new)
    student_id: str | None = None  # Optional student ID for logging
    research_interests: list[str] = Field(default_factory=list)  # Legacy format
    abstract: str | None = None  # Legacy format
    top_k: int = 5
    min_similarity: float = 0.45


class SupervisorMatch(BaseModel):
    supervisor_id: int
    name: str
    email: str
    department: str
    research_cluster: str
    research_interests: list[str]
    similarity_score: float
    multi_factor_score: float
    explanation: str
    availability: bool
    current_students: int
    max_students: int


class MatchSupervisorsResponse(BaseModel):
    matches: list[SupervisorMatch]


@router.post("/supervisors", response_model=MatchSupervisorsResponse)
async def match_supervisors(req: MatchSupervisorsRequest) -> MatchSupervisorsResponse:
    """
    Find top-K supervisors for a student research proposal.

    Uses fine-tuned SBERT model trained on SLIIT supervisors + student proposals.

    Args:
        proposal: Free-text research proposal (recommended)
        research_interests: Legacy — array of interest keywords
        abstract: Legacy — research abstract
        top_k: Number of supervisors to return (default 5)
        min_similarity: Minimum similarity threshold (default 0.45)

    Returns:
        List of ranked supervisor matches with explanation
    """
    # Build query text
    if req.proposal:
        query_text = req.proposal
    else:
        # Legacy support: build from interests + abstract
        query_parts = list(req.research_interests)
        if req.abstract:
            query_parts.append(req.abstract)
        query_text = ". ".join(query_parts) if query_parts else "general research"

    if not query_text or not query_text.strip():
        logger.warning("Empty proposal provided")
        return MatchSupervisorsResponse(matches=[])

    try:
        # Call the supervisor matching service
        matches = await find_supervisors(
            student_proposal=query_text,
            top_k=req.top_k,
            min_similarity=req.min_similarity,
        )

        # Convert to response schema
        response_matches = [
            SupervisorMatch(
                supervisor_id=m["supervisor_id"],
                name=m["name"],
                email=m["email"],
                department=m["department"],
                research_cluster=m["research_cluster"],
                research_interests=m["research_interests"],
                similarity_score=m["similarity_score"],
                multi_factor_score=m["multi_factor_score"],
                explanation=m["explanation"],
                availability=m["availability"],
                current_students=m["current_students"],
                max_students=m["max_students"],
            )
            for m in matches
        ]

        logger.info(f"Found {len(response_matches)} supervisor matches for proposal")
        return MatchSupervisorsResponse(matches=response_matches)

    except Exception as e:
        logger.error(f"Supervisor matching failed: {e}", exc_info=True)
        return MatchSupervisorsResponse(matches=[])


# ─── Supervisor publications via Semantic Scholar ──────────────────────────

_SLIIT_JSON = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "sliit_supervisors.json")
)
_sliit_data: list[dict] | None = None


def _load_sliit() -> list[dict]:
    global _sliit_data
    if _sliit_data is None:
        try:
            with open(_SLIIT_JSON, encoding="utf-8") as f:
                _sliit_data = json.load(f)
        except Exception as exc:
            logger.error("Cannot load sliit_supervisors.json: %s", exc)
            _sliit_data = []
    return _sliit_data


def _get_sliit_supervisor(sid: int) -> dict | None:
    return next((s for s in _load_sliit() if s.get("id") == sid), None)


_ss_cache: dict[int, tuple[list, float]] = {}
_SS_TTL: float = 3600.0


class PaperEntry(BaseModel):
    paper_id: str = ""
    title: str
    year: Optional[int] = None
    venue: Optional[str] = None
    url: Optional[str] = None
    doi: Optional[str] = None


class SupervisorPapersResponse(BaseModel):
    supervisor_id: int
    name: str
    department: str
    research_interests: list[str]
    papers: list[PaperEntry]
    total: int
    year_distribution: dict[str, int]
    topic_distribution: list[dict]


async def _query_semantic_scholar(name: str) -> list[dict]:
    """Fetch papers from Semantic Scholar by author name (best-effort)."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            for query in [f"{name} SLIIT", name]:
                r = await client.get(
                    "https://api.semanticscholar.org/graph/v1/author/search",
                    params={"query": query, "fields": "name,papers", "limit": 3},
                )
                authors = r.json().get("data", []) if r.status_code == 200 else []
                if authors:
                    break

            if not authors:
                return []

            author_id = authors[0].get("authorId", "")
            if not author_id:
                return []

            rp = await client.get(
                f"https://api.semanticscholar.org/graph/v1/author/{author_id}/papers",
                params={"fields": "title,year,venue,externalIds,openAccessPdf", "limit": 50},
            )
            return rp.json().get("data", []) if rp.status_code == 200 else []
    except Exception as exc:
        logger.warning("Semantic Scholar API error for '%s': %s", name, exc)
        return []


@router.get("/supervisors/{supervisor_id}/papers", response_model=SupervisorPapersResponse)
async def get_supervisor_papers(supervisor_id: int) -> SupervisorPapersResponse:
    """Return publications and visual analytics for a SLIIT supervisor."""
    supervisor = _get_sliit_supervisor(supervisor_id)
    if not supervisor:
        raise HTTPException(status_code=404, detail=f"Supervisor {supervisor_id} not found")

    cached = _ss_cache.get(supervisor_id)
    if cached and (time.time() - cached[1]) < _SS_TTL:
        raw_papers = cached[0]
    else:
        raw_papers = await _query_semantic_scholar(supervisor["name"])
        _ss_cache[supervisor_id] = (raw_papers, time.time())

    papers: list[PaperEntry] = []
    for p in raw_papers:
        ext = p.get("externalIds") or {}
        doi = ext.get("DOI")
        oap = p.get("openAccessPdf") or {}
        url = oap.get("url") or (f"https://doi.org/{doi}" if doi else None)
        if not url and p.get("paperId"):
            url = f"https://www.semanticscholar.org/paper/{p['paperId']}"
        papers.append(PaperEntry(
            paper_id=p.get("paperId") or "",
            title=p.get("title") or "Untitled",
            year=p.get("year"),
            venue=(p.get("venue") or "").strip() or None,
            url=url,
            doi=doi,
        ))

    papers.sort(key=lambda x: x.year or 0, reverse=True)

    year_dist: dict[str, int] = {}
    for p in papers:
        if p.year and p.year >= 2010:
            k = str(p.year)
            year_dist[k] = year_dist.get(k, 0) + 1

    research_interests: list[str] = supervisor.get("research_interests", [])
    topic_dist = [{"name": ri, "value": 1} for ri in research_interests[:10]]

    return SupervisorPapersResponse(
        supervisor_id=supervisor_id,
        name=supervisor.get("name", ""),
        department=supervisor.get("department", ""),
        research_interests=research_interests,
        papers=papers,
        total=len(papers),
        year_distribution=dict(sorted(year_dist.items())),
        topic_distribution=topic_dist,
    )
