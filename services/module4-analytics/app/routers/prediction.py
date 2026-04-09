"""Success prediction endpoint — RF + XGBoost ensemble."""

from typing import Literal
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class PredictRequest(BaseModel):
    proposal_id: str
    user_id: str


class RiskFactor(BaseModel):
    factor: str
    severity: Literal["low", "medium", "high", "critical"]
    description: str


class PredictResponse(BaseModel):
    proposal_id: str
    success_probability: float
    risk_level: Literal["low", "medium", "high", "critical"]
    risk_factors: list[RiskFactor]
    recommendations: list[str]
    model_type: str


@router.post("/predict", response_model=PredictResponse)
async def predict(req: PredictRequest) -> PredictResponse:
    """Run RF + XGBoost soft-voting ensemble to predict success likelihood.

    Features (per spec): milestone completion rate, engagement metrics,
    quality score trajectory, supervisor interaction frequency,
    topic trend alignment, peer collaboration score.
    Target: F1 > 0.75, ROC-AUC > 0.80.
    """
    return PredictResponse(
        proposal_id=req.proposal_id,
        success_probability=0.0,
        risk_level="low",
        risk_factors=[],
        recommendations=[],
        model_type="rf+xgboost-stub",
    )
