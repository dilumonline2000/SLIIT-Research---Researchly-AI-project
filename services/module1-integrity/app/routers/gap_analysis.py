"""Gap analysis endpoint.

Primary path: locally-trained gap analyzer (SBERT retrieval over 4,219 SLIIT papers).
Fallback path: Gemini prompt — only used when no local index is available.

Each gap returned cites the SLIIT paper(s) it came from, so users get
evidence-grounded research gaps instead of free-text speculation.
"""

from __future__ import annotations

import logging
import os
import sys

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()
logger = logging.getLogger(__name__)

_services_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, _services_root)


class AnalyzeGapsRequest(BaseModel):
    topic: str = Field(..., min_length=1)
    top_k: int = 8
    min_similarity: float = 0.25


class SupportingPaper(BaseModel):
    paper_id: str = ""
    title: str = ""
    authors: list[str] = []
    year: int | str | None = None
    url: str = ""


class ResearchGap(BaseModel):
    topic: str
    description: str
    gap_score: float
    recency_score: float
    novelty_score: float
    similarity: float = 0.0
    gap_type: str = ""
    supporting_paper: SupportingPaper | None = None
    supporting_paper_ids: list[str] = []  # kept for backwards-compat


class AnalyzeGapsResponse(BaseModel):
    gaps: list[ResearchGap]
    total_papers_analyzed: int = 0
    total_corpus_size: int = 0
    model_version: str = "unknown"
    base_model: str = "unknown"
    source: str = "unknown"  # "local" | "gemini" | "fallback"


@router.post("/analyze", response_model=AnalyzeGapsResponse)
async def analyze_gaps(req: AnalyzeGapsRequest) -> AnalyzeGapsResponse:
    """Identify research gaps for the given topic.

    Strategy:
      1. Try the local trained gap analyzer (preferred — grounded in SLIIT papers).
      2. If unavailable, fall back to Gemini.
      3. If both fail, return an empty list.
    """
    # ── 1. Local model ───────────────────────────────────────────────────────
    try:
        from app.services import gap_analyzer

        result = gap_analyzer.analyze(req.topic, top_k=req.top_k, min_similarity=req.min_similarity)
        if result.get("loaded") and result.get("gaps"):
            gaps = [
                ResearchGap(
                    topic=g["topic"],
                    description=g["description"],
                    gap_score=g["gap_score"],
                    recency_score=g["recency_score"],
                    novelty_score=g["novelty_score"],
                    similarity=g.get("similarity", 0.0),
                    gap_type=g.get("gap_type", ""),
                    supporting_paper=SupportingPaper(**g["supporting_paper"]) if g.get("supporting_paper") else None,
                    supporting_paper_ids=[g["supporting_paper"]["paper_id"]]
                        if g.get("supporting_paper", {}).get("paper_id") else [],
                )
                for g in result["gaps"]
            ]
            return AnalyzeGapsResponse(
                gaps=gaps,
                total_papers_analyzed=result.get("total_papers_analyzed", 0),
                total_corpus_size=result.get("total_corpus_size", 0),
                model_version=result.get("model_version", "unknown"),
                base_model=result.get("base_model", "unknown"),
                source="local",
            )
        if result.get("loaded") and not result.get("gaps"):
            logger.info("Local gap analyzer loaded but no matches above threshold for: %s", req.topic)
    except Exception as e:
        logger.warning("Local gap analyzer failed: %s — falling back to Gemini", e)

    # ── 2. Gemini fallback ───────────────────────────────────────────────────
    try:
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

        data = generate_json(prompt)
        raw_gaps = data.get("gaps", [])
        gaps = [
            ResearchGap(
                topic=g.get("topic", ""),
                description=g.get("description", ""),
                gap_score=round(float(g.get("gap_score", 0.5)), 3),
                recency_score=round(float(g.get("recency_score", 0.5)), 3),
                novelty_score=round(float(g.get("novelty_score", 0.5)), 3),
                supporting_paper=None,
                supporting_paper_ids=[],
            )
            for g in raw_gaps
            if g.get("topic")
        ]
        gaps.sort(key=lambda g: g.novelty_score, reverse=True)
        return AnalyzeGapsResponse(gaps=gaps[:8], source="gemini")
    except Exception as e:
        logger.error("Gemini gap analysis also failed: %s", e)

    return AnalyzeGapsResponse(gaps=[], source="fallback")


@router.get("/status")
async def gap_analyzer_status() -> dict:
    """Health check for the local gap analyzer model."""
    try:
        from app.services import gap_analyzer
        return gap_analyzer.get_model_info()
    except Exception as e:
        return {"loaded": False, "error": str(e)}
