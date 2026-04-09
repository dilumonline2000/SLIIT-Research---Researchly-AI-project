"""Shared text preprocessing helpers for ML pipelines."""

import re
import unicodedata


def clean_text(text: str) -> str:
    """Unicode-normalize, collapse whitespace, strip."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_sentences(text: str) -> list[str]:
    """Naive sentence splitter — replace with spaCy for production quality."""
    text = clean_text(text)
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)
    return [s.strip() for s in sentences if s.strip()]


def truncate_tokens(text: str, max_words: int = 512) -> str:
    """Word-level truncation safe for BERT-family tokenizers (~1.3x words)."""
    words = text.split()
    return " ".join(words[:max_words])
