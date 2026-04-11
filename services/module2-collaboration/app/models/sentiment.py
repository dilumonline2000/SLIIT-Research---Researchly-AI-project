"""Model wrapper for Aspect-Based Sentiment Analysis — inference time."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import torch
import torch.nn as nn
from transformers import AutoTokenizer, AutoModel

logger = logging.getLogger(__name__)

DEFAULT_MODEL_DIR = Path(__file__).parent.parent.parent / "models" / "sentiment"

ASPECTS = ["methodology", "writing", "originality", "data_analysis"]
LABELS = ["positive", "neutral", "negative"]


class _AspectSentimentNet(nn.Module):
    """Mirror of the training architecture for loading weights."""

    def __init__(self, base_model: str, num_aspects: int = 4, num_classes: int = 3, dropout: float = 0.3):
        super().__init__()
        self.encoder = AutoModel.from_pretrained(base_model)
        hidden_size = self.encoder.config.hidden_size
        self.aspect_heads = nn.ModuleList([
            nn.Sequential(
                nn.Linear(hidden_size, 256),
                nn.ReLU(),
                nn.Dropout(dropout),
                nn.Linear(256, num_classes),
            )
            for _ in range(num_aspects)
        ])

    def forward(self, input_ids, attention_mask):
        outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        cls_output = outputs.last_hidden_state[:, 0, :]
        return [head(cls_output) for head in self.aspect_heads]


class AspectSentimentModel:
    """Wrapper for the trained aspect-based sentiment model."""

    def __init__(self, model_dir: str | Path | None = None):
        self.model_dir = Path(model_dir) if model_dir else DEFAULT_MODEL_DIR
        self._model = None
        self._tokenizer = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def load(self) -> None:
        """Load the trained model."""
        config_file = self.model_dir / "label_config.json"
        base_model = "bert-base-uncased"

        if config_file.exists():
            with open(config_file) as f:
                config = json.load(f)
        else:
            config = {"aspects": ASPECTS, "labels": LABELS}

        self._tokenizer = AutoTokenizer.from_pretrained(str(self.model_dir) if (self.model_dir / "tokenizer_config.json").exists() else base_model)
        self._model = _AspectSentimentNet(base_model, num_aspects=len(config["aspects"]))

        weights_path = self.model_dir / "model.pt"
        if weights_path.exists():
            self._model.load_state_dict(torch.load(weights_path, map_location=self.device, weights_only=True))
            logger.info("Loaded sentiment model from %s", self.model_dir)
        else:
            logger.warning("No trained weights found at %s", weights_path)

        self._model = self._model.to(self.device).eval()

    @property
    def model(self):
        if self._model is None:
            self.load()
        return self._model

    @property
    def tokenizer(self):
        if self._tokenizer is None:
            self.load()
        return self._tokenizer

    def analyze(self, text: str) -> dict[str, dict[str, float]]:
        """Analyze feedback text for per-aspect sentiment.

        Returns: {aspect: {positive: prob, neutral: prob, negative: prob}}
        """
        encoding = self.tokenizer(text, max_length=512, padding="max_length", truncation=True, return_tensors="pt")
        input_ids = encoding["input_ids"].to(self.device)
        attention_mask = encoding["attention_mask"].to(self.device)

        with torch.no_grad():
            logits_list = self.model(input_ids, attention_mask)

        results = {}
        for i, aspect in enumerate(ASPECTS):
            probs = torch.softmax(logits_list[i], dim=-1).squeeze().cpu().tolist()
            results[aspect] = {label: round(prob, 4) for label, prob in zip(LABELS, probs)}
        return results
