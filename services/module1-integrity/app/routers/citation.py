"""Citation parsing, formatting, lookup, and reference-list endpoints.

Endpoints
---------
  POST /citations/parse              – raw text → structured fields + IEEE/APA + warnings
  POST /citations/format             – structured fields + style → formatted string
  POST /citations/lookup-doi         – DOI → CrossRef metadata
  POST /citations/lookup-title       – Title → CrossRef candidates (top-K)
  POST /citations/in-text            – structured fields + style + index → in-text
  POST /citations/reference-list     – list of fields + style → numbered/sorted list
  POST /citations/similar-papers     – topic / title → SLIIT papers nearest in SBERT space
"""

from __future__ import annotations

import logging
import os
import sys
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()
logger = logging.getLogger(__name__)

_services_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, _services_root)


# ─── Schemas ──────────────────────────────────────────────────────────────


class ParsedCitation(BaseModel):
    raw: str = ""
    source_type: str = "journal"
    authors: list[str] = []
    title: str = ""
    year: Optional[int] = None
    journal: Optional[str] = None
    conference: Optional[str] = None
    publisher: Optional[str] = None
    url: Optional[str] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    doi: Optional[str] = None
    edition: Optional[str] = None


class ParseRequest(BaseModel):
    raw_text: str = Field(..., min_length=1)


class ParseResponse(BaseModel):
    parsed: ParsedCitation
    formatted_apa: str
    formatted_ieee: str
    in_text_apa: str
    in_text_ieee: str
    warnings: list[str] = []
    confidence: float
    source: str = "regex"  # "regex" | "crossref"


class FormatRequest(BaseModel):
    parsed: ParsedCitation
    style: str = Field("apa", pattern="^(apa|ieee|APA|IEEE)$")


class FormatResponse(BaseModel):
    formatted: str
    style: str
    in_text: str


class DoiRequest(BaseModel):
    doi: str = Field(..., min_length=3)


class TitleSearchRequest(BaseModel):
    title: str = Field(..., min_length=4)
    limit: int = 5


class InTextRequest(BaseModel):
    parsed: ParsedCitation
    style: str = "apa"
    index: int = 1


class ReferenceListRequest(BaseModel):
    entries: list[ParsedCitation]
    style: str = "apa"


class ReferenceListResponse(BaseModel):
    style: str
    entries: list[str]


class SimilarPapersRequest(BaseModel):
    query: str = Field(..., min_length=3)
    top_k: int = 5


class SimilarPaper(BaseModel):
    paper_id: str = ""
    title: str = ""
    authors: list[str] = []
    year: Optional[int] = None
    url: str = ""
    similarity: float = 0.0
    abstract_excerpt: str = ""


# ─── Helpers ──────────────────────────────────────────────────────────────


def _confidence(parsed: dict[str, Any]) -> float:
    weights = {
        "authors": 0.25,
        "title": 0.25,
        "year": 0.15,
        "journal": 0.10,
        "conference": 0.10,
        "publisher": 0.10,
        "url": 0.05,
        "doi": 0.10,
    }
    score = 0.0
    if parsed.get("authors"):
        score += weights["authors"]
    for field in ("title", "year", "doi"):
        if parsed.get(field):
            score += weights[field]
    src = parsed.get("source_type")
    if src == "journal" and parsed.get("journal"):
        score += weights["journal"]
    elif src == "conference" and parsed.get("conference"):
        score += weights["conference"]
    elif src == "book" and parsed.get("publisher"):
        score += weights["publisher"]
    elif src == "website" and parsed.get("url"):
        score += weights["url"]
    return round(min(1.0, score), 2)


def _to_response(parsed: dict[str, Any], source: str = "regex") -> ParseResponse:
    from app.services import citation_engine

    return ParseResponse(
        parsed=ParsedCitation(**parsed),
        formatted_apa=citation_engine.format_apa(parsed),
        formatted_ieee=citation_engine.format_ieee(parsed),
        in_text_apa=citation_engine.in_text(parsed, "apa"),
        in_text_ieee=citation_engine.in_text(parsed, "ieee"),
        warnings=citation_engine.missing_fields(parsed),
        confidence=_confidence(parsed),
        source=source,
    )


# ─── Endpoints ────────────────────────────────────────────────────────────


@router.post("/parse", response_model=ParseResponse)
async def parse(req: ParseRequest) -> ParseResponse:
    """Parse a raw citation string into structured fields + IEEE/APA outputs."""
    from app.services import citation_engine
    parsed = citation_engine.parse(req.raw_text)
    return _to_response(parsed, source="regex")


@router.post("/format", response_model=FormatResponse)
async def format_citation(req: FormatRequest) -> FormatResponse:
    """Format a structured record in the requested style."""
    from app.services import citation_engine
    style = req.style.lower()
    parsed = req.parsed.model_dump()
    return FormatResponse(
        formatted=citation_engine.format_citation(parsed, style),
        style=style,
        in_text=citation_engine.in_text(parsed, style),
    )


@router.post("/lookup-doi", response_model=ParseResponse)
async def lookup_doi(req: DoiRequest) -> ParseResponse:
    """Fetch metadata for a DOI from CrossRef and return formatted citations."""
    try:
        from app.services import crossref_lookup
        rec = crossref_lookup.lookup_doi(req.doi)
    except Exception as e:
        logger.error("CrossRef lookup error: %s", e)
        rec = None
    if not rec:
        raise HTTPException(status_code=404, detail=f"No record found for DOI {req.doi}")
    return _to_response(rec, source="crossref")


@router.post("/lookup-title")
async def lookup_title(req: TitleSearchRequest) -> dict[str, Any]:
    """Return candidate CrossRef matches for a title query."""
    from app.services import citation_engine, crossref_lookup
    candidates = crossref_lookup.search_title(req.title, limit=req.limit)
    out = []
    for c in candidates:
        out.append({
            "parsed": c,
            "formatted_apa": citation_engine.format_apa(c),
            "formatted_ieee": citation_engine.format_ieee(c),
        })
    return {"candidates": out, "count": len(out)}


@router.post("/in-text")
async def gen_in_text(req: InTextRequest) -> dict[str, str]:
    from app.services import citation_engine
    return {"in_text": citation_engine.in_text(req.parsed.model_dump(), req.style, req.index)}


@router.post("/reference-list", response_model=ReferenceListResponse)
async def reference_list(req: ReferenceListRequest) -> ReferenceListResponse:
    from app.services import citation_engine
    entries = [e.model_dump() for e in req.entries]
    style = req.style.lower()
    rendered = citation_engine.build_reference_list(entries, style)
    return ReferenceListResponse(style=style, entries=rendered)


@router.post("/similar-papers")
async def similar_papers(req: SimilarPapersRequest) -> dict[str, Any]:
    """Find SLIIT papers similar to the user's query (title or topic)."""
    try:
        from app.services import sliit_examples
        results = sliit_examples.similar_papers(req.query, top_k=req.top_k)
    except Exception as e:
        logger.warning("Similar-papers lookup failed: %s", e)
        results = []
    return {"papers": [SimilarPaper(**r).model_dump() for r in results], "count": len(results)}
