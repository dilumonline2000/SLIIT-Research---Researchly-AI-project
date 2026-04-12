"""Research paper summarizer — BART/T5 abstractive summaries."""

from __future__ import annotations

import logging
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ..models.summarizer import SummarizerModel

router = APIRouter()
logger = logging.getLogger(__name__)

_summarizer: SummarizerModel | None = None


def _get_summarizer() -> SummarizerModel:
    global _summarizer
    if _summarizer is None:
        _summarizer = SummarizerModel()
    return _summarizer


LENGTH_CONFIG = {
    "short": {"max_length": 80, "min_length": 20},
    "medium": {"max_length": 180, "min_length": 50},
    "detailed": {"max_length": 350, "min_length": 100},
}


class SummarizeRequest(BaseModel):
    text: str = Field(..., min_length=100)
    length: Literal["short", "medium", "detailed"] = "medium"
    paper_id: str | None = None


class SummarizeResponse(BaseModel):
    summary: str
    model_version: str
    rouge_scores: dict[str, float] | None = None


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize(req: SummarizeRequest) -> SummarizeResponse:
    """Generate an abstractive summary using BART + LoRA.

    1. Select length parameters based on requested level
    2. Run BART model generation
    3. Optionally store summary in Supabase
    """
    model = _get_summarizer()
    config = LENGTH_CONFIG[req.length]

    try:
        summary = model.summarize(
            req.text,
            max_length=config["max_length"],
            min_length=config["min_length"],
        )
    except Exception as e:
        logger.error("Summarization failed: %s", e)
        return SummarizeResponse(summary="", model_version="bart-v1-error")

    # Store if paper_id provided
    if req.paper_id and summary:
        try:
            import sys, os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "shared"))
            from services.shared.supabase_client import get_supabase_admin
            sb = get_supabase_admin()
            sb.table("research_summaries").upsert({
                "paper_id": req.paper_id,
                "summary": summary,
                "summary_type": req.length,
                "model_version": "bart-v1",
            }).execute()
        except Exception as e:
            logger.warning("Failed to store summary: %s", e)

    return SummarizeResponse(summary=summary, model_version="bart-v1")
