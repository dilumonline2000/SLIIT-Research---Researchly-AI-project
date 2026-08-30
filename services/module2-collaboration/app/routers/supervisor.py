"""Supervisor matching endpoint — fine-tuned SBERT + multi-factor scoring."""

from __future__ import annotations

import asyncio
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
    min_similarity: float = 0.2


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


_ss_cache: dict[int, tuple[list, float, bool]] = {}
_SS_TTL: float = 3600.0          # successful (non-empty or genuinely-empty) lookups
_SS_FAILURE_TTL: float = 90.0    # rate-limited / errored lookups — retry soon instead of for an hour


class PaperEntry(BaseModel):
    paper_id: str = ""
    title: str
    year: Optional[int] = None
    venue: Optional[str] = None
    url: Optional[str] = None
    doi: Optional[str] = None


class ResearchFocus(BaseModel):
    summary: str
    recent_focus_areas: list[str] = []
    activity_level: str = ""


class SupervisorPapersResponse(BaseModel):
    supervisor_id: int
    name: str
    department: str
    research_interests: list[str]
    papers: list[PaperEntry]
    total: int
    year_distribution: dict[str, int]
    topic_distribution: list[dict]
    research_focus: Optional[ResearchFocus] = None


def _s2_headers() -> dict:
    key = os.environ.get("SEMANTIC_SCHOLAR_API_KEY", "")
    return {"x-api-key": key} if key else {}


# Semantic Scholar's rate limit is 1 request/second, CUMULATIVE across all
# endpoints and all concurrent callers of this process. A single supervisor
# lookup already needs 2-3 sequential calls (author search retry + papers
# fetch), so without spacing them out the 2nd/3rd call reliably 429s. This
# lock+timestamp pair serializes every Semantic Scholar call process-wide.
_S2_LOCK = asyncio.Lock()
_S2_LAST_CALL: float = 0.0
_S2_MIN_INTERVAL = 1.05


async def _s2_get(client: httpx.AsyncClient, url: str, params: dict) -> httpx.Response:
    """GET with process-wide pacing plus backoff retries on 429.

    Semantic Scholar's free/keyed tier is easy to trip (1 req/s, shared across
    every caller of the key — not just this process). A single 429 doesn't
    mean "no data", so we retry a few times with increasing delay before
    giving up.
    """
    global _S2_LAST_CALL
    last_resp: httpx.Response | None = None
    for attempt in range(3):
        async with _S2_LOCK:
            wait = _S2_MIN_INTERVAL - (time.time() - _S2_LAST_CALL)
            if wait > 0:
                await asyncio.sleep(wait)
            try:
                last_resp = await client.get(url, params=params)
            finally:
                _S2_LAST_CALL = time.time()
        if last_resp.status_code != 429:
            return last_resp
        await asyncio.sleep(1.5 * (attempt + 1))
    return last_resp


async def _query_semantic_scholar(name: str) -> tuple[list[dict], bool]:
    """Fetch papers from Semantic Scholar by author name (best-effort).

    Returns (papers, ok) — ok=False means the lookup failed/rate-limited
    (as opposed to succeeding with a genuinely empty result), so the caller
    can avoid caching a transient failure for a long time.
    """
    try:
        headers = _s2_headers()
        async with httpx.AsyncClient(timeout=15.0, headers=headers) as client:
            # A bare name search matches Semantic Scholar's author index far
            # more reliably than appending "SLIIT" (which searches for that
            # literal string as part of the author's name and rarely hits).
            # One query instead of two also halves the calls spent per
            # lookup, which matters a lot under a 1 req/s shared limit.
            r = await _s2_get(
                client,
                "https://api.semanticscholar.org/graph/v1/author/search",
                {"query": name, "fields": "name,papers", "limit": 5},
            )
            if r.status_code == 429:
                logger.warning("Semantic Scholar rate limit hit for '%s'", name)
                return [], False
            authors = r.json().get("data", []) if r.status_code == 200 else []

            if not authors:
                return [], True

            author_id = authors[0].get("authorId", "")
            if not author_id:
                return [], True

            rp = await _s2_get(
                client,
                f"https://api.semanticscholar.org/graph/v1/author/{author_id}/papers",
                {"fields": "title,year,venue,externalIds,openAccessPdf", "limit": 50},
            )
            if rp.status_code == 429:
                logger.warning("Semantic Scholar rate limit hit fetching papers for '%s'", name)
                return [], False
            if rp.status_code != 200:
                return [], False
            return rp.json().get("data", []), True
    except Exception as exc:
        logger.warning("Semantic Scholar API error for '%s': %s", name, exc)
        return [], False


# ─── AI-generated "recent research focus" summary ──────────────────────────
# LLM calls are far more expensive than a Semantic Scholar lookup, so a
# successful summary is cached much longer (a supervisor's research focus
# doesn't shift hour to hour) and is strictly best-effort: any failure just
# omits the field, it never breaks the existing papers/charts response.
#
# Gemini frequently returns a transient 503 ("model overloaded"). Caching that
# miss for the full 24h — as an earlier version did — is why the summary would
# render on one deployment (which happened to get a success) but stay blank for
# a whole day on another (which cached a failure on its first call). So a miss
# is cached only briefly and retried on the next view, mirroring the
# success/failure split already used for the Semantic Scholar cache above.

_focus_cache: dict[int, tuple[Optional[dict], float]] = {}
_FOCUS_TTL: float = 86_400.0     # 24h — successful summary
_FOCUS_FAILURE_TTL: float = 300.0  # 5 min — transient LLM failure, retry soon


def _generate_research_focus(name: str, papers: list[PaperEntry]) -> Optional[dict]:
    if not papers:
        return None
    try:
        from shared.gemini_client import generate_json

        recent = [p for p in papers if p.title][:15]
        paper_lines = "\n".join(
            f"- {p.title} ({p.year or 'year unknown'})" for p in recent
        )
        prompt = f"""You are helping a student decide whether to pick this research supervisor.

Supervisor: {name}
Their recent publications (most recent first):
{paper_lines}

Based only on these titles and years, analyze what this supervisor has actually
been researching lately and how active they currently are.

Return JSON:
{{
  "summary": "2-3 sentence plain-language summary of what they've recently worked on and whether it's a good time to approach them",
  "recent_focus_areas": ["short topic", "short topic", "short topic"],
  "activity_level": "Actively publishing" | "Occasional publications" | "Limited recent activity"
}}"""
        data = generate_json(prompt)
        if not isinstance(data, dict) or not data.get("summary"):
            return None
        return {
            "summary": str(data.get("summary", "")).strip(),
            "recent_focus_areas": [str(a) for a in (data.get("recent_focus_areas") or [])][:5],
            "activity_level": str(data.get("activity_level", "")).strip(),
        }
    except Exception as exc:
        logger.warning("Gemini research-focus summary failed for '%s': %s", name, exc)
        return None


@router.get("/supervisors/{supervisor_id}/papers", response_model=SupervisorPapersResponse)
async def get_supervisor_papers(supervisor_id: int) -> SupervisorPapersResponse:
    """Return publications and visual analytics for a SLIIT supervisor."""
    supervisor = _get_sliit_supervisor(supervisor_id)
    if not supervisor:
        raise HTTPException(status_code=404, detail=f"Supervisor {supervisor_id} not found")

    cached = _ss_cache.get(supervisor_id)
    if cached:
        cached_papers, cached_at, cached_ok = cached
        ttl = _SS_TTL if cached_ok else _SS_FAILURE_TTL
        if (time.time() - cached_at) < ttl:
            raw_papers = cached_papers
        else:
            raw_papers, ok = await _query_semantic_scholar(supervisor["name"])
            _ss_cache[supervisor_id] = (raw_papers, time.time(), ok)
    else:
        raw_papers, ok = await _query_semantic_scholar(supervisor["name"])
        _ss_cache[supervisor_id] = (raw_papers, time.time(), ok)

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

    focus_cached = _focus_cache.get(supervisor_id)
    if focus_cached:
        cached_focus, cached_focus_at = focus_cached
        focus_ttl = _FOCUS_TTL if cached_focus else _FOCUS_FAILURE_TTL
        fresh = (time.time() - cached_focus_at) < focus_ttl
    else:
        cached_focus, fresh = None, False

    if fresh:
        focus_data = cached_focus
    else:
        focus_data = _generate_research_focus(supervisor.get("name", ""), papers)
        _focus_cache[supervisor_id] = (focus_data, time.time())

    return SupervisorPapersResponse(
        supervisor_id=supervisor_id,
        name=supervisor.get("name", ""),
        department=supervisor.get("department", ""),
        research_interests=research_interests,
        papers=papers,
        total=len(papers),
        year_distribution=dict(sorted(year_dist.items())),
        topic_distribution=topic_dist,
        research_focus=ResearchFocus(**focus_data) if focus_data else None,
    )
