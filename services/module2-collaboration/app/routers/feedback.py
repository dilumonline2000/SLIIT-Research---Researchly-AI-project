"""Aspect-based sentiment analysis for academic feedback."""

from __future__ import annotations

import logging

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ..models.sentiment import AspectSentimentModel

router = APIRouter()
logger = logging.getLogger(__name__)

_sentiment_model: AspectSentimentModel | None = None


def _get_model() -> AspectSentimentModel:
    global _sentiment_model
    if _sentiment_model is None:
        _sentiment_model = AspectSentimentModel()
    return _sentiment_model


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
    """Run aspect-based BERT sentiment classifier.

    1. Feed feedback text through the 4-head BERT model
    2. Get per-aspect sentiment probabilities
    3. Pick the dominant class per aspect
    4. Aggregate into overall sentiment
    """
    model = _get_model()

    try:
        results = model.analyze(req.feedback_text)
    except Exception as e:
        logger.error("Sentiment analysis failed: %s", e)
        return AnalyzeFeedbackResponse(
            overall_sentiment="neutral",
            overall_score=0.0,
            aspects=AspectSentiment(
                methodology="neutral", writing="neutral",
                originality="neutral", data_analysis="neutral",
            ),
        )

    # Pick dominant class per aspect
    aspect_labels = {}
    sentiment_scores = []
    SCORE_MAP = {"positive": 1.0, "neutral": 0.0, "negative": -1.0}

    for aspect, probs in results.items():
        dominant = max(probs, key=probs.get)
        aspect_labels[aspect] = dominant
        sentiment_scores.append(SCORE_MAP.get(dominant, 0.0))

    # Overall sentiment
    avg_score = sum(sentiment_scores) / max(len(sentiment_scores), 1)
    if avg_score > 0.3:
        overall = "positive"
    elif avg_score < -0.3:
        overall = "negative"
    else:
        overall = "neutral"

    return AnalyzeFeedbackResponse(
        overall_sentiment=overall,
        overall_score=round(avg_score, 3),
        aspects=AspectSentiment(**aspect_labels),
        aspect_probabilities=results,
    )
