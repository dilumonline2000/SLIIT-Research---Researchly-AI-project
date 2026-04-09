"""Research paper summarizer — BART/T5 abstractive summaries."""

from typing import Literal
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()


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
    """Generate an abstractive summary.

    TODO (Phase 3): Load fine-tuned BART-large-cnn with LoRA adapter,
    call model.generate() with length-specific max_length.
    """
    return SummarizeResponse(summary="", model_version="bart-v0-stub")
