"""Gap analysis — powered by Gemini with optional pgvector context."""

from __future__ import annotations

import logging
import sys
import os

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()
logger = logging.getLogger(__name__)

_services_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, _services_root)


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
    """Identify research gaps using Gemini AI analysis."""
    from shared.gemini_client import generate_json

    prompt = f"""You are an expert research analyst. Identify the top research gaps for the topic: "{req.topic}"

Analyze what areas are under-explored, what methodologies are missing, and what future directions exist.

Return a JSON array of exactly 5-8 research gaps:
{{
  "gaps": [
    {{
      "topic": "specific gap topic",
      "description": "detailed description of why this is a gap and what research is needed",
      "gap_score": 0.85,
      "recency_score": 0.7,
      "novelty_score": 0.8
    }}
  ]
}}

gap_score: 0.0-1.0 (1.0 = major unexplored gap)
recency_score: 0.0-1.0 (1.0 = very outdated/stale research)
novelty_score: 0.0-1.0 (1.0 = highly novel opportunity)"""

    try:
        data = generate_json(prompt)
        raw_gaps = data.get("gaps", [])
        gaps = [
            ResearchGap(
                topic=g.get("topic", ""),
                description=g.get("description", ""),
                gap_score=round(float(g.get("gap_score", 0.5)), 3),
                recency_score=round(float(g.get("recency_score", 0.5)), 3),
                novelty_score=round(float(g.get("novelty_score", 0.5)), 3),
                supporting_paper_ids=[],
            )
            for g in raw_gaps
            if g.get("topic")
        ]
        gaps.sort(key=lambda g: g.novelty_score, reverse=True)
        return AnalyzeGapsResponse(gaps=gaps[:8], total_papers_analyzed=0)
    except Exception as e:
        logger.error("Gemini gap analysis failed: %s", e)
        return AnalyzeGapsResponse(gaps=[], total_papers_analyzed=0)
