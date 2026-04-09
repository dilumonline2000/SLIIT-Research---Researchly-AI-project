"""Topic categorization endpoint — SciBERT multi-label classifier."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()


class CategorizeRequest(BaseModel):
    text: str = Field(..., min_length=1)
    paper_id: str | None = None


class CategorizeResponse(BaseModel):
    categories: list[str]
    confidence_scores: dict[str, float]
    model_version: str


@router.post("/categorize", response_model=CategorizeResponse)
async def categorize(req: CategorizeRequest) -> CategorizeResponse:
    """Classify a paper/abstract into research categories.

    TODO (Phase 3): Load fine-tuned SciBERT head, run inference,
    threshold at 0.5 for multi-label assignment, return labels + scores.
    """
    return CategorizeResponse(
        categories=[],
        confidence_scores={},
        model_version="scibert-v0-stub",
    )
