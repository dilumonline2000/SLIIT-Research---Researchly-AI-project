"""Plagiarism checker — TF-IDF + SBERT similarity against research_papers corpus."""

from typing import Literal
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()


class CheckPlagiarismRequest(BaseModel):
    text: str = Field(..., min_length=10)
    threshold: float = Field(0.8, ge=0.0, le=1.0)


class FlaggedPassage(BaseModel):
    text: str
    matched_source: str
    similarity_score: float


class CheckPlagiarismResponse(BaseModel):
    risk_level: Literal["low", "medium", "high"]
    overall_score: float
    flagged_passages: list[FlaggedPassage]


@router.post("/check", response_model=CheckPlagiarismResponse)
async def check_plagiarism(req: CheckPlagiarismRequest) -> CheckPlagiarismResponse:
    """Run TF-IDF + SBERT similarity check.

    TODO (Phase 4): Chunk input, embed each chunk, query pgvector against
    research_papers.embedding, return matches above threshold.
    """
    return CheckPlagiarismResponse(
        risk_level="low",
        overall_score=0.0,
        flagged_passages=[],
    )
