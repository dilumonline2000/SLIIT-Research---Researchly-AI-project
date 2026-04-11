"""Model wrapper for Citation NER (spaCy) — inference time."""

from __future__ import annotations

import logging
from pathlib import Path

import spacy

logger = logging.getLogger(__name__)

DEFAULT_MODEL_DIR = Path(__file__).parent.parent.parent / "models" / "citation_ner"


class CitationNERModel:
    """Wrapper for the trained spaCy NER model for citation entity extraction."""

    ENTITIES = ["AUTHOR", "TITLE", "JOURNAL", "YEAR", "VOLUME", "PAGES", "DOI"]

    def __init__(self, model_dir: str | Path | None = None):
        self.model_dir = Path(model_dir) if model_dir else DEFAULT_MODEL_DIR
        self._nlp = None

    def load(self) -> None:
        """Load the trained spaCy model."""
        if self.model_dir.exists():
            self._nlp = spacy.load(str(self.model_dir))
            logger.info("Loaded citation NER model from %s", self.model_dir)
        else:
            logger.warning("Model not found at %s, using blank model", self.model_dir)
            self._nlp = spacy.blank("en")

    @property
    def nlp(self):
        if self._nlp is None:
            self.load()
        return self._nlp

    def extract_entities(self, citation_text: str) -> list[dict]:
        """Extract citation entities from a reference string.

        Returns list of {"text": str, "label": str, "start": int, "end": int}.
        """
        doc = self.nlp(citation_text)
        return [
            {
                "text": ent.text,
                "label": ent.label_,
                "start": ent.start_char,
                "end": ent.end_char,
            }
            for ent in doc.ents
            if ent.label_ in self.ENTITIES
        ]

    def parse_citation(self, citation_text: str) -> dict:
        """Parse a citation into structured fields."""
        entities = self.extract_entities(citation_text)
        parsed = {}
        for ent in entities:
            label = ent["label"].lower()
            if label in parsed:
                if isinstance(parsed[label], list):
                    parsed[label].append(ent["text"])
                else:
                    parsed[label] = [parsed[label], ent["text"]]
            else:
                parsed[label] = ent["text"]
        return parsed
