"""Aspect-based sentiment analysis for academic feedback — powered by Gemini."""

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


class AnalyzeFeedbackRequest(BaseModel):
    feedback_text: str = Field(..., min_length=1)


class AspectSentiment(BaseModel):
    methodology: str  # positive | neutral | negative
    writing: str
    originality: str
    data_analysis: str


class AnalyzeFeedbackResponse(BaseModel):
    overall_sentiment: str
    overall_score: float
    aspects: AspectSentiment
    aspect_probabilities: dict | None = None


@router.post("/analyze", response_model=AnalyzeFeedbackResponse)
async def analyze_feedback(req: AnalyzeFeedbackRequest) -> AnalyzeFeedbackResponse:
    """Analyze academic feedback sentiment across 4 aspects using Gemini."""
    from shared.gemini_client import generate_json

    prompt = f"""Analyze this academic research feedback for sentiment across four aspects.

Feedback: {req.feedback_text}

For each aspect, determine the sentiment: "positive", "neutral", or "negative".
Also provide a probability score for each sentiment (must sum to 1.0 per aspect).

Return JSON:
{{
  "methodology": {{"sentiment": "positive", "positive": 0.8, "neutral": 0.15, "negative": 0.05}},
  "writing": {{"sentiment": "neutral", "positive": 0.3, "neutral": 0.5, "negative": 0.2}},
  "originality": {{"sentiment": "positive", "positive": 0.7, "neutral": 0.2, "negative": 0.1}},
  "data_analysis": {{"sentiment": "negative", "positive": 0.1, "neutral": 0.2, "negative": 0.7}},
  "overall_sentiment": "positive",
  "overall_score": 0.4
}}

overall_score: -1.0 (very negative) to 1.0 (very positive)"""

    try:
        data = generate_json(prompt)

        SCORE_MAP = {"positive": 1.0, "neutral": 0.0, "negative": -1.0}
        aspect_labels = {}
        aspect_probs = {}

        for aspect in ["methodology", "writing", "originality", "data_analysis"]:
            aspect_data = data.get(aspect, {})
            sentiment = aspect_data.get("sentiment", "neutral")
            aspect_labels[aspect] = sentiment
            aspect_probs[aspect] = {
                "positive": float(aspect_data.get("positive", 0.33)),
                "neutral": float(aspect_data.get("neutral", 0.34)),
                "negative": float(aspect_data.get("negative", 0.33)),
            }

        scores = [SCORE_MAP.get(s, 0.0) for s in aspect_labels.values()]
        avg_score = sum(scores) / max(len(scores), 1)

        overall = data.get("overall_sentiment", "neutral")
        if overall not in ("positive", "neutral", "negative"):
            overall = "positive" if avg_score > 0.3 else ("negative" if avg_score < -0.3 else "neutral")

        return AnalyzeFeedbackResponse(
            overall_sentiment=overall,
            overall_score=round(float(data.get("overall_score", avg_score)), 3),
            aspects=AspectSentiment(**aspect_labels),
            aspect_probabilities=aspect_probs,
        )

    except Exception as e:
        logger.error("Gemini feedback analysis failed: %s", e)
        return AnalyzeFeedbackResponse(
            overall_sentiment="neutral",
            overall_score=0.0,
            aspects=AspectSentiment(
                methodology="neutral", writing="neutral",
                originality="neutral", data_analysis="neutral",
            ),
        )
