"""Citation parsing + formatting endpoints (NER → APA/IEEE)."""

from __future__ import annotations

import logging
import re

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..models.citation_ner import CitationNERModel

router = APIRouter()
logger = logging.getLogger(__name__)

# Lazy-loaded singleton
_ner_model: CitationNERModel | None = None


def _get_ner() -> CitationNERModel:
    global _ner_model
    if _ner_model is None:
        _ner_model = CitationNERModel()
    return _ner_model


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


def _entities_to_parsed(entities: list[dict]) -> ParsedCitation:
    """Convert NER entity list into ParsedCitation."""
    authors: list[str] = []
    title = ""
    journal = None
    year = None
    volume = None
    pages = None
    doi = None

    for ent in entities:
        label = ent["label"]
        text = ent["text"].strip()
        if label == "AUTHOR":
            # Split compound author strings
            for a in re.split(r"\s+and\s+|,\s*(?=[A-Z])", text):
                a = a.strip().rstrip(",")
                if a:
                    authors.append(a)
        elif label == "TITLE":
            title = text.rstrip(".")
        elif label == "JOURNAL":
            journal = text
        elif label == "YEAR":
            try:
                year = int(re.search(r"\d{4}", text).group())
            except (AttributeError, ValueError):
                pass
        elif label == "VOLUME":
            volume = text
        elif label == "PAGES":
            pages = text
        elif label == "DOI":
            doi = text

    return ParsedCitation(
        authors=authors, title=title, journal=journal,
        year=year, volume=volume, pages=pages, doi=doi,
    )


def _format_apa(p: ParsedCitation) -> str:
    """Format parsed citation as APA 7th edition."""
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
    """Format parsed citation as IEEE style."""
    parts = []
    if p.authors:
        # IEEE uses initials first: J. Smith
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
    """Parse a raw citation string into structured entities using spaCy NER."""
    if not req.raw_text.strip():
        raise HTTPException(status_code=400, detail="raw_text cannot be empty")

    ner = _get_ner()
    entities = ner.extract_entities(req.raw_text)

    parsed = _entities_to_parsed(entities)

    # If NER returned nothing, try regex fallback
    if not parsed.authors and not parsed.title:
        parsed = _regex_fallback(req.raw_text)

    # Confidence based on how many fields were extracted
    filled = sum([
        bool(parsed.authors), bool(parsed.title), bool(parsed.journal),
        parsed.year is not None, bool(parsed.volume), bool(parsed.pages), bool(parsed.doi),
    ])
    confidence = min(filled / 5.0, 1.0)

    return ParseCitationResponse(
        parsed=parsed,
        formatted_apa=_format_apa(parsed),
        formatted_ieee=_format_ieee(parsed),
        confidence=round(confidence, 2),
    )


def _regex_fallback(text: str) -> ParsedCitation:
    """Basic regex extraction when NER has no trained weights."""
    authors: list[str] = []
    title = ""
    year = None
    doi = None

    # Year
    year_match = re.search(r"\((\d{4})\)", text)
    if year_match:
        year = int(year_match.group(1))

    # DOI
    doi_match = re.search(r"(10\.\d{4,}[^\s]+)", text)
    if doi_match:
        doi = doi_match.group(1)

    # Authors: text before first (year) or first period
    if year_match:
        author_chunk = text[:year_match.start()].strip().rstrip(".(")
    else:
        author_chunk = text.split(".")[0].strip()
    if author_chunk:
        for a in re.split(r"\s+and\s+|;\s*|,\s+&\s+", author_chunk):
            a = a.strip().rstrip(",")
            if a and len(a) > 2:
                authors.append(a)

    # Title: text between year and next period/journal
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
    """Format parsed entities into APA or IEEE."""
    if req.style == "apa":
        formatted = _format_apa(req.parsed)
    else:
        formatted = _format_ieee(req.parsed)
    return {"formatted": formatted, "style": req.style}
