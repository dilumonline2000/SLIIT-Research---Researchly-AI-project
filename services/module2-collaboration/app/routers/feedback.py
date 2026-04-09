"""Aspect-based sentiment analysis for academic feedback."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()


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


@router.post("/analyze", response_model=AnalyzeFeedbackResponse)
async def analyze_feedback(req: AnalyzeFeedbackRequest) -> AnalyzeFeedbackResponse:
    """Run aspect-based BERT sentiment classifier.

    TODO (Phase 3/4): Load fine-tuned BERT with per-aspect heads, run inference,
    aggregate into overall sentiment.
    """
    return AnalyzeFeedbackResponse(
        overall_sentiment="neutral",
        overall_score=0.0,
        aspects=AspectSentiment(
            methodology="neutral",
            writing="neutral",
            originality="neutral",
            data_analysis="neutral",
        ),
    )
