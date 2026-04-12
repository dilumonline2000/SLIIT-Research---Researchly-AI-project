"""Topic categorization endpoint — SciBERT multi-label classifier."""

from __future__ import annotations

import logging

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ..models.topic_classifier import TopicClassifierModel

router = APIRouter()
logger = logging.getLogger(__name__)

_classifier: TopicClassifierModel | None = None


def _get_classifier() -> TopicClassifierModel:
    global _classifier
    if _classifier is None:
        _classifier = TopicClassifierModel()
    return _classifier


class CategorizeRequest(BaseModel):
    text: str = Field(..., min_length=1)
    paper_id: str | None = None
    threshold: float = Field(0.5, ge=0.0, le=1.0)


class CategorizeResponse(BaseModel):
    categories: list[str]
    confidence_scores: dict[str, float]
    model_version: str


@router.post("/categorize", response_model=CategorizeResponse)
async def categorize(req: CategorizeRequest) -> CategorizeResponse:
    """Classify a paper/abstract into research categories using SciBERT.

    1. Feed text through SciBERT multi-label classifier
    2. Threshold at requested level for multi-label assignment
    3. Optionally update paper record in Supabase
    """
    classifier = _get_classifier()

    try:
        results = classifier.classify(req.text, threshold=req.threshold)
    except Exception as e:
        logger.error("Classification failed: %s", e)
        return CategorizeResponse(categories=[], confidence_scores={}, model_version="scibert-v1-error")

    categories = [r["category"] for r in results]
    scores = {r["category"]: r["confidence"] for r in results}

    # If paper_id provided, update the record in Supabase
    if req.paper_id and categories:
        try:
            import sys, os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "shared"))
            from services.shared.supabase_client import get_supabase_admin
            sb = get_supabase_admin()
            sb.table("research_papers").update({"keywords": categories}).eq("id", req.paper_id).execute()
        except Exception as e:
            logger.warning("Failed to update paper categories: %s", e)

    return CategorizeResponse(
        categories=categories,
        confidence_scores=scores,
        model_version="scibert-v1",
    )
