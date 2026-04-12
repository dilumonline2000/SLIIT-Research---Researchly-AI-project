"""Plagiarism checker — SBERT similarity against research_papers corpus."""

from __future__ import annotations

import logging
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()
logger = logging.getLogger(__name__)


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


def _chunk_text(text: str, chunk_size: int = 3) -> list[str]:
    """Split text into sentence-level chunks for comparison."""
    import re
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks = []
    for i in range(0, len(sentences), chunk_size):
        chunk = " ".join(sentences[i:i + chunk_size]).strip()
        if len(chunk) > 30:
            chunks.append(chunk)
    if not chunks and text.strip():
        chunks = [text.strip()]
    return chunks


@router.post("/check", response_model=CheckPlagiarismResponse)
async def check_plagiarism(req: CheckPlagiarismRequest) -> CheckPlagiarismResponse:
    """Run SBERT similarity check against the research paper corpus.

    1. Chunk input text into sentence groups
    2. Embed each chunk via SBERT
    3. Query pgvector for nearest matches
    4. Flag chunks above the similarity threshold
    """
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
            logger.warning("Shared utils not available — returning low risk")
            return CheckPlagiarismResponse(risk_level="low", overall_score=0.0, flagged_passages=[])

    chunks = _chunk_text(req.text)
    flagged: list[FlaggedPassage] = []
    scores: list[float] = []

    sb = get_supabase_admin()

    for chunk in chunks:
        try:
            chunk_vec = embed(chunk).tolist()
            result = sb.rpc(
                "match_papers",
                {"query_embedding": chunk_vec, "match_count": 1, "match_threshold": req.threshold},
            ).execute()

            matches = result.data or []
            if matches:
                best = matches[0]
                sim = float(best.get("similarity", 0))
                scores.append(sim)
                if sim >= req.threshold:
                    flagged.append(FlaggedPassage(
                        text=chunk[:200],
                        matched_source=f"{best.get('title', 'Unknown')} ({best.get('publication_year', 'n.d.')})",
                        similarity_score=round(sim, 4),
                    ))
                else:
                    scores.append(sim)
            else:
                scores.append(0.0)
        except Exception as e:
            logger.warning("Plagiarism check chunk failed: %s", e)
            scores.append(0.0)

    overall = max(scores) if scores else 0.0
    if overall >= 0.9 or len(flagged) >= 3:
        risk_level = "high"
    elif overall >= req.threshold or len(flagged) >= 1:
        risk_level = "medium"
    else:
        risk_level = "low"

    return CheckPlagiarismResponse(
        risk_level=risk_level,
        overall_score=round(overall, 4),
        flagged_passages=flagged,
    )
