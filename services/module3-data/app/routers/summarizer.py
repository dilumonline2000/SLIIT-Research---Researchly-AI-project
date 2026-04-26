"""Research paper summarizer — powered by Gemini."""

from __future__ import annotations

import logging
import sys
import os
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()
logger = logging.getLogger(__name__)

_services_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, _services_root)

LENGTH_INSTRUCTIONS = {
    "short": "Write a concise 2-3 sentence summary capturing only the most essential points.",
    "medium": "Write a paragraph (4-6 sentences) covering the main contributions, methodology, and findings.",
    "detailed": "Write a comprehensive summary (8-10 sentences) covering background, objectives, methodology, results, and conclusions.",
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
    """Generate an abstractive summary using Gemini."""
    from shared.gemini_client import generate

    instruction = LENGTH_INSTRUCTIONS[req.length]
    text_snippet = req.text[:6000]

    prompt = f"""You are an expert academic summarizer. {instruction}

Research text:
{text_snippet}

Write only the summary, no preamble or labels."""

    try:
        summary = generate(prompt, temperature=0.3, max_tokens=512)

        if req.paper_id and summary:
            try:
                from shared.supabase_client import get_supabase_admin
                sb = get_supabase_admin()
                sb.table("research_summaries").upsert({
                    "paper_id": req.paper_id,
                    "summary": summary,
                    "summary_type": req.length,
                    "model_version": "gemini-2.5-flash",
                }).execute()
            except Exception as e:
                logger.warning("Failed to store summary: %s", e)

        return SummarizeResponse(summary=summary, model_version="gemini-2.5-flash")

    except Exception as e:
        logger.error("Gemini summarization failed: %s", e)
        return SummarizeResponse(summary="", model_version="gemini-error")
