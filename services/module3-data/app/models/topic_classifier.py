"""Model wrapper for SciBERT Multi-label Topic Classifier — inference time."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from transformers import AutoTokenizer, AutoModel

logger = logging.getLogger(__name__)

DEFAULT_MODEL_DIR = Path(__file__).parent.parent.parent / "models" / "scibert_classifier"

CATEGORIES = [
    "Artificial Intelligence", "Internet of Things", "Networking",
    "Cybersecurity", "Data Science", "Machine Learning",
    "Mobile Computing", "Cloud Computing", "Software Engineering",
    "Computer Vision", "Natural Language Processing",
    "Information Retrieval", "Databases",
    "Human-Computer Interaction", "Other",
]


class _SciBERTClassifierNet(nn.Module):
    """Mirror of the training architecture."""

    def __init__(self, base_model: str, num_labels: int, dropout: float = 0.3):
        super().__init__()
        self.encoder = AutoModel.from_pretrained(base_model)
        hidden_size = self.encoder.config.hidden_size
        self.classifier = nn.Sequential(
            nn.Linear(hidden_size, 512),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(512, num_labels),
        )

    def forward(self, input_ids, attention_mask):
        outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        token_embeddings = outputs.last_hidden_state
        mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        pooled = torch.sum(token_embeddings * mask_expanded, dim=1) / torch.clamp(mask_expanded.sum(dim=1), min=1e-9)
        return self.classifier(pooled)


class TopicClassifierModel:
    """Wrapper for the trained SciBERT topic classifier."""

    def __init__(self, model_dir: str | Path | None = None):
        self.model_dir = Path(model_dir) if model_dir else DEFAULT_MODEL_DIR
        self._model = None
        self._tokenizer = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.categories = CATEGORIES

    def load(self) -> None:
        base_model = "allenai/scibert_scivocab_uncased"
        labels_file = self.model_dir / "label_classes.json"
        if labels_file.exists():
            with open(labels_file) as f:
                self.categories = json.load(f)

        self._tokenizer = AutoTokenizer.from_pretrained(
            str(self.model_dir) if (self.model_dir / "tokenizer_config.json").exists() else base_model
        )
        self._model = _SciBERTClassifierNet(base_model, num_labels=len(self.categories))

        weights_path = self.model_dir / "model.pt"
        if weights_path.exists():
            self._model.load_state_dict(torch.load(weights_path, map_location=self.device, weights_only=True))
            logger.info("Loaded topic classifier from %s", self.model_dir)
        else:
            logger.warning("No trained weights at %s", weights_path)

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

    def classify(self, text: str, threshold: float = 0.5) -> list[dict]:
        """Classify a paper into topic categories.

        Returns list of {category: str, confidence: float} sorted by confidence.
        """
        encoding = self.tokenizer(text, max_length=512, padding="max_length", truncation=True, return_tensors="pt")
        input_ids = encoding["input_ids"].to(self.device)
        attention_mask = encoding["attention_mask"].to(self.device)

        with torch.no_grad():
            logits = self.model(input_ids, attention_mask)
            probs = torch.sigmoid(logits).squeeze().cpu().numpy()

        results = []
        for i, (cat, prob) in enumerate(zip(self.categories, probs)):
            if prob >= threshold:
                results.append({"category": cat, "confidence": round(float(prob), 4)})

        return sorted(results, key=lambda x: x["confidence"], reverse=True)
