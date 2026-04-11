"""Model wrapper for Success Predictor (RF + XGBoost) — inference time."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import joblib

logger = logging.getLogger(__name__)

DEFAULT_MODEL_DIR = Path(__file__).parent.parent.parent / "models" / "prediction"

FEATURES = [
    "milestone_completion_rate",
    "login_frequency",
    "submission_frequency",
    "quality_score_trajectory",
    "supervisor_interaction_frequency",
    "topic_trend_alignment",
    "peer_collaboration_score",
    "citation_count",
    "feedback_sentiment_avg",
    "days_since_last_submission",
]


class SuccessPredictorModel:
    """Wrapper for the trained RF + XGBoost success predictor."""

    def __init__(self, model_dir: str | Path | None = None):
        self.model_dir = Path(model_dir) if model_dir else DEFAULT_MODEL_DIR
        self._model = None
        self._scaler = None

    def load(self) -> None:
        model_path = self.model_dir / "ensemble_model.pkl"
        scaler_path = self.model_dir / "scaler.pkl"

        if model_path.exists():
            self._model = joblib.load(model_path)
            logger.info("Loaded success predictor from %s", model_path)
        else:
            logger.warning("No model found at %s", model_path)

        if scaler_path.exists():
            self._scaler = joblib.load(scaler_path)

    @property
    def model(self):
        if self._model is None:
            self.load()
        return self._model

    @property
    def scaler(self):
        if self._scaler is None:
            self.load()
        return self._scaler

    def predict(self, features: dict[str, float]) -> dict:
        """Predict research success probability.

        Args:
            features: Dict with keys matching FEATURES list.

        Returns: {prediction: str, probability: float, risk_factors: list}
        """
        if self.model is None:
            return {"error": "Model not loaded"}

        # Build feature vector in correct order
        feature_vector = np.array([[features.get(f, 0.0) for f in FEATURES]])

        if self.scaler is not None:
            feature_vector = self.scaler.transform(feature_vector)

        probability = self.model.predict_proba(feature_vector)[0][1]
        prediction = "success" if probability >= 0.5 else "at_risk"

        # Identify risk factors (features contributing to low probability)
        risk_factors = []
        if prediction == "at_risk":
            for f in FEATURES:
                val = features.get(f, 0.0)
                if f == "days_since_last_submission" and val > 30:
                    risk_factors.append({"factor": f, "value": val, "concern": "Long gap since last submission"})
                elif f == "milestone_completion_rate" and val < 0.4:
                    risk_factors.append({"factor": f, "value": val, "concern": "Low milestone completion"})
                elif f == "quality_score_trajectory" and val < 0:
                    risk_factors.append({"factor": f, "value": val, "concern": "Declining quality scores"})
                elif f == "supervisor_interaction_frequency" and val < 0.5:
                    risk_factors.append({"factor": f, "value": val, "concern": "Infrequent supervisor meetings"})

        return {
            "prediction": prediction,
            "probability": round(float(probability), 4),
            "risk_factors": risk_factors,
        }
