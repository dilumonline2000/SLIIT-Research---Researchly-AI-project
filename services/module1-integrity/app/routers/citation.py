"""Citation parsing + formatting endpoints (NER → APA/IEEE)."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()


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


@router.post("/parse", response_model=ParseCitationResponse)
async def parse_citation(req: ParseCitationRequest) -> ParseCitationResponse:
    """Parse a raw citation string into structured entities.

    TODO (Phase 3): Load fine-tuned spaCy NER model and extract entities.
    Current scaffold returns an empty stub so the end-to-end pipeline works.
    """
    if not req.raw_text.strip():
        raise HTTPException(status_code=400, detail="raw_text cannot be empty")

    # Placeholder — wire spaCy NER pipeline in Phase 3
    parsed = ParsedCitation()
    return ParseCitationResponse(
        parsed=parsed,
        formatted_apa="",
        formatted_ieee="",
        confidence=0.0,
    )


class FormatRequest(BaseModel):
    parsed: ParsedCitation
    style: str = Field("apa", pattern="^(apa|ieee)$")


@router.post("/format")
async def format_citation(req: FormatRequest) -> dict:
    """Format parsed entities into APA or IEEE. Stub pending Phase 4."""
    return {"formatted": "", "style": req.style}
