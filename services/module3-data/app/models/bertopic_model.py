"""Model wrapper for BERTopic — inference time."""

from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_MODEL_DIR = Path(__file__).parent.parent.parent / "models" / "bertopic"


class BERTopicModel:
    """Wrapper for the trained BERTopic model."""

    def __init__(self, model_dir: str | Path | None = None):
        self.model_dir = Path(model_dir) if model_dir else DEFAULT_MODEL_DIR
        self._model = None

    def load(self) -> None:
        try:
            from bertopic import BERTopic
            model_path = self.model_dir / "bertopic_model"
            if model_path.exists():
                self._model = BERTopic.load(str(model_path))
                logger.info("Loaded BERTopic model from %s", model_path)
            else:
                logger.warning("No BERTopic model found at %s", model_path)
        except ImportError:
            logger.error("bertopic not installed — pip install bertopic")

    @property
    def model(self):
        if self._model is None:
            self.load()
        return self._model

    def get_topics(self, texts: list[str]) -> list[dict]:
        """Assign topics to documents.

        Returns list of {topic_id: int, topic_words: list, probability: float}.
        """
        if self.model is None:
            return [{"topic_id": -1, "topic_words": [], "probability": 0.0} for _ in texts]

        topics, probs = self.model.transform(texts)
        results = []
        for topic_id, prob in zip(topics, probs):
            words = []
            if topic_id != -1:
                topic_words = self.model.get_topic(topic_id)
                words = [w for w, _ in topic_words[:10]]
            results.append({
                "topic_id": int(topic_id),
                "topic_words": words,
                "probability": float(prob) if not isinstance(prob, list) else float(max(prob)),
            })
        return results

    def get_topic_info(self) -> list[dict]:
        """Get summary of all discovered topics."""
        if self.model is None:
            return []
        info = self.model.get_topic_info()
        return info.to_dict(orient="records")
