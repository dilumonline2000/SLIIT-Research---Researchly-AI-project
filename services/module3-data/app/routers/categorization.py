"""Topic categorization endpoint — powered by Gemini."""

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

RESEARCH_CATEGORIES = [
    "Machine Learning", "Deep Learning", "Natural Language Processing",
    "Computer Vision", "Data Mining", "Knowledge Graphs", "Bioinformatics",
    "Cybersecurity", "Human-Computer Interaction", "Software Engineering",
    "Distributed Systems", "Cloud Computing", "IoT", "Robotics",
    "Quantum Computing", "Algorithms", "Databases", "Networking",
    "Healthcare Informatics", "Education Technology",
]


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
    """Classify research text into categories using Gemini."""
    from shared.gemini_client import generate_json

    categories_list = ", ".join(RESEARCH_CATEGORIES)

    prompt = f"""Classify this research text into relevant academic categories.

Text: {req.text[:3000]}

Available categories: {categories_list}

Select all relevant categories and assign a confidence score (0.0-1.0) to each.
Only include categories with confidence >= {req.threshold}.

Return JSON:
{{
  "classifications": [
    {{"category": "Machine Learning", "confidence": 0.92}},
    {{"category": "Natural Language Processing", "confidence": 0.78}}
  ]
}}"""

    try:
        data = generate_json(prompt)
        classifications = data.get("classifications", [])

        categories = []
        scores = {}
        for item in classifications:
            cat = item.get("category", "")
            conf = float(item.get("confidence", 0.0))
            if cat and conf >= req.threshold:
                categories.append(cat)
                scores[cat] = round(conf, 3)

        if req.paper_id and categories:
            try:
                from shared.supabase_client import get_supabase_admin
                sb = get_supabase_admin()
                sb.table("research_papers").update({"keywords": categories}).eq("id", req.paper_id).execute()
            except Exception as e:
                logger.warning("Failed to update paper categories: %s", e)

        return CategorizeResponse(
            categories=categories,
            confidence_scores=scores,
            model_version="gemini-2.5-flash",
        )

    except Exception as e:
        logger.error("Gemini categorization failed: %s", e)
        return CategorizeResponse(categories=[], confidence_scores={}, model_version="gemini-error")
