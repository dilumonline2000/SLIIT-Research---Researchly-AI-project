"""Topic categorization endpoint.

Primary path: locally-trained TF-IDF + LogReg multi-label classifier
              (services/module3-data/models/trained_topic_classifier/)
Fallback path: Gemini prompt — only when the local bundle is missing.
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


class CategorizeRequest(BaseModel):
    text: str = Field(..., min_length=1)
    paper_id: str | None = None
    threshold: float = Field(0.3, ge=0.0, le=1.0)
    top_k: int = 5


class TopCategory(BaseModel):
    label: str
    confidence: float


class RelatedPaper(BaseModel):
    paper_id: str = ""
    title: str = ""
    authors: list[str] = []
    year: int | str | None = None
    url: str = ""
    subject: str | list[str] | None = None
    similarity: float = 0.0
    abstract_excerpt: str = ""


class CategorizeResponse(BaseModel):
    categories: list[str]
    confidence_scores: dict[str, float]
    top_categories: list[TopCategory] = []
    related_papers: list[RelatedPaper] = []
    model_version: str
    source: str = "unknown"  # "local" | "gemini" | "fallback"


def _related_papers(text: str, top_k: int = 5) -> list[RelatedPaper]:
    """Best-effort SLIIT-paper retrieval. Empty list if the index isn't loaded."""
    try:
        from app.services import paper_index
        rows = paper_index.find_related(text, top_k=top_k, min_similarity=0.18)
        return [RelatedPaper(**r) for r in rows]
    except Exception as e:
        logger.warning("Related-paper lookup failed: %s", e)
        return []


@router.post("/categorize", response_model=CategorizeResponse)
async def categorize(req: CategorizeRequest) -> CategorizeResponse:
    """Multi-label classify the given text into research categories."""

    # ── 1. Local model ───────────────────────────────────────────────────────
    try:
        from app.services import topic_classifier

        result = topic_classifier.classify(req.text, threshold=req.threshold, top_k=req.top_k)
        if result.get("loaded"):
            if req.paper_id and result["categories"]:
                try:
                    from shared.supabase_client import get_supabase_admin
                    sb = get_supabase_admin()
                    sb.table("research_papers").update({"keywords": result["categories"]}).eq("id", req.paper_id).execute()
                except Exception as e:
                    logger.warning("Failed to update paper categories: %s", e)
            return CategorizeResponse(
                categories=result["categories"],
                confidence_scores=result["confidence_scores"],
                top_categories=[TopCategory(**tc) for tc in result.get("top_categories", [])],
                related_papers=_related_papers(req.text, top_k=6),
                model_version=f"local-tfidf-logreg-{result.get('model_version','1.0.0')}",
                source="local",
            )
    except Exception as e:
        logger.warning("Local topic classifier failed: %s — falling back to Gemini", e)

    # ── 2. Gemini fallback ───────────────────────────────────────────────────
    try:
        from shared.gemini_client import generate_json

        prompt = f"""Classify this research text into relevant academic categories.

Text: {req.text[:3000]}

Return JSON with all relevant categories and confidence scores (0.0-1.0):
{{
  "classifications": [
    {{"category": "Machine Learning", "confidence": 0.92}}
  ]
}}"""
        data = generate_json(prompt)
        classifications = data.get("classifications", [])
        cats: list[str] = []
        scores: dict[str, float] = {}
        top: list[TopCategory] = []
        for item in classifications:
            cat = item.get("category", "")
            conf = float(item.get("confidence", 0.0))
            if not cat:
                continue
            top.append(TopCategory(label=cat, confidence=round(conf, 3)))
            if conf >= req.threshold:
                cats.append(cat)
                scores[cat] = round(conf, 3)
        return CategorizeResponse(
            categories=cats,
            confidence_scores=scores,
            top_categories=top[: req.top_k],
            related_papers=_related_papers(req.text, top_k=6),
            model_version="gemini-2.5-flash",
            source="gemini",
        )
    except Exception as e:
        logger.error("Gemini categorization also failed: %s", e)

    return CategorizeResponse(
        categories=[], confidence_scores={}, top_categories=[],
        model_version="fallback", source="fallback",
    )


@router.get("/categorize/status")
async def categorize_status() -> dict:
    try:
        from app.services import topic_classifier
        return topic_classifier.get_model_info()
    except Exception as e:
        return {"loaded": False, "error": str(e)}
