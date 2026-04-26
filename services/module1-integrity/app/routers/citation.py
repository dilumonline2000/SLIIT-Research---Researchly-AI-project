"""Citation parsing + formatting endpoints — powered by Gemini."""

from __future__ import annotations

import logging
import re
import sys
import os

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()
logger = logging.getLogger(__name__)

_services_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, _services_root)


def _get_gemini():
    from shared.gemini_client import generate_json
    return generate_json


class ParseCitationRequest(BaseModel):
    raw_text: str = Field(..., min_length=1, description="Raw citation string")


class ParsedCitation(BaseModel):
    authors: list[str] = []
    title: str = ""
    journal: str | None = None
    year: int | None = None
    volume: str | None = None
    pages: str | None = None
    doi: str | None = None


class ParseCitationResponse(BaseModel):
    parsed: ParsedCitation
    formatted_apa: str
    formatted_ieee: str
    confidence: float


def _format_apa(p: ParsedCitation) -> str:
    parts = []
    if p.authors:
        parts.append(", ".join(p.authors))
    if p.year:
        parts.append(f"({p.year})")
    if p.title:
        parts.append(f"{p.title}.")
    if p.journal:
        journal_part = f"*{p.journal}*"
        if p.volume:
            journal_part += f", *{p.volume}*"
        if p.pages:
            journal_part += f", {p.pages}"
        parts.append(f"{journal_part}.")
    if p.doi:
        doi_clean = p.doi if p.doi.startswith("http") else f"https://doi.org/{p.doi.replace('doi:', '').strip()}"
        parts.append(doi_clean)
    return " ".join(parts)


def _format_ieee(p: ParsedCitation) -> str:
    parts = []
    if p.authors:
        parts.append(", ".join(p.authors) + ",")
    if p.title:
        parts.append(f'"{p.title},"')
    if p.journal:
        parts.append(f"*{p.journal}*,")
    if p.volume:
        parts.append(f"vol. {p.volume},")
    if p.pages:
        parts.append(f"pp. {p.pages},")
    if p.year:
        parts.append(f"{p.year}.")
    if p.doi:
        parts.append(f"doi: {p.doi}.")
    return " ".join(parts)


@router.post("/parse", response_model=ParseCitationResponse)
async def parse_citation(req: ParseCitationRequest) -> ParseCitationResponse:
    if not req.raw_text.strip():
        raise HTTPException(status_code=400, detail="raw_text cannot be empty")

    prompt = f"""Parse this academic citation into structured fields.

Citation: {req.raw_text}

Return JSON with exactly these fields:
{{
  "authors": ["Author Name 1", "Author Name 2"],
  "title": "Paper title here",
  "journal": "Journal name or null",
  "year": 2023,
  "volume": "volume number or null",
  "pages": "page range or null",
  "doi": "doi string or null"
}}

If a field is not present, use null for objects and empty array for authors."""

    try:
        generate_json = _get_gemini()
        data = generate_json(prompt)
        parsed = ParsedCitation(
            authors=data.get("authors") or [],
            title=data.get("title") or "",
            journal=data.get("journal"),
            year=data.get("year"),
            volume=str(data["volume"]) if data.get("volume") else None,
            pages=str(data["pages"]) if data.get("pages") else None,
            doi=data.get("doi"),
        )
    except Exception as e:
        logger.error("Gemini citation parse failed: %s", e)
        parsed = _regex_fallback(req.raw_text)

    filled = sum([
        bool(parsed.authors), bool(parsed.title), bool(parsed.journal),
        parsed.year is not None, bool(parsed.doi),
    ])
    confidence = min(filled / 5.0, 1.0)

    return ParseCitationResponse(
        parsed=parsed,
        formatted_apa=_format_apa(parsed),
        formatted_ieee=_format_ieee(parsed),
        confidence=round(confidence, 2),
    )


def _regex_fallback(text: str) -> ParsedCitation:
    authors: list[str] = []
    title = ""
    year = None
    doi = None

    year_match = re.search(r"\((\d{4})\)", text)
    if year_match:
        year = int(year_match.group(1))

    doi_match = re.search(r"(10\.\d{4,}[^\s]+)", text)
    if doi_match:
        doi = doi_match.group(1)

    if year_match:
        author_chunk = text[:year_match.start()].strip().rstrip(".(")
    else:
        author_chunk = text.split(".")[0].strip()
    if author_chunk:
        for a in re.split(r"\s+and\s+|;\s*|,\s+&\s+", author_chunk):
            a = a.strip().rstrip(",")
            if a and len(a) > 2:
                authors.append(a)

    if year_match:
        rest = text[year_match.end():].strip().lstrip(")., ")
        title_match = re.match(r"(.+?)\.", rest)
        if title_match:
            title = title_match.group(1).strip()

    return ParsedCitation(authors=authors, title=title, year=year, doi=doi)


class FormatRequest(BaseModel):
    parsed: ParsedCitation
    style: str = Field("apa", pattern="^(apa|ieee)$")


@router.post("/format")
async def format_citation(req: FormatRequest) -> dict:
    if req.style == "apa":
        formatted = _format_apa(req.parsed)
    else:
        formatted = _format_ieee(req.parsed)
    return {"formatted": formatted, "style": req.style}
