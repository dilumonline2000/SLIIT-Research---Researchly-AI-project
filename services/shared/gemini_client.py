"""Shared Gemini client used by all 5 Python services."""

import os
import json
import time
import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)

_API_KEY: Optional[str] = None
_MODEL: str = "gemini-2.5-flash"
# Ordered fallback chain — tried in sequence on 429
_FALLBACK_MODELS: list = ["gemini-2.0-flash", "gemini-flash-latest", "gemini-flash-lite-latest"]
_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"


def _get_key() -> str:
    global _API_KEY
    if not _API_KEY:
        _API_KEY = os.environ.get("GEMINI_API_KEY", "")
        if not _API_KEY:
            raise RuntimeError("GEMINI_API_KEY not set in environment")
    return _API_KEY


def _get_model() -> str:
    return os.environ.get("GEMINI_MODEL", _MODEL)


def generate(prompt: str, temperature: float = 0.3, max_tokens: int = 2048) -> str:
    """Call Gemini generateContent and return the text response.

    Retries once with the fallback model on 429 rate-limit errors so a
    temporarily exhausted quota on the primary model doesn't break chat.
    """
    key = _get_key()
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        },
    }

    models_to_try = [_get_model()] + _FALLBACK_MODELS
    last_exc: Optional[Exception] = None

    for attempt, model in enumerate(models_to_try):
        url = f"{_BASE_URL}/{model}:generateContent?key={key}"
        try:
            r = requests.post(url, json=payload, timeout=60)
            if r.status_code == 429:
                logger.warning("Gemini 429 on %s (attempt %d/%d)",
                               model, attempt + 1, len(models_to_try))
                if attempt < len(models_to_try) - 1:
                    time.sleep(1)
                    continue
                raise requests.exceptions.HTTPError(response=r)
            r.raise_for_status()
            data = r.json()
            try:
                return data["candidates"][0]["content"]["parts"][0]["text"].strip()
            except (KeyError, IndexError) as e:
                raise RuntimeError(f"Unexpected Gemini response: {data}") from e
        except requests.exceptions.HTTPError as exc:
            last_exc = exc
            if attempt < len(models_to_try) - 1:
                continue
    raise last_exc or RuntimeError("All Gemini models exhausted")


def generate_json(prompt: str, temperature: float = 0.1) -> dict:
    """Call Gemini and parse the response as JSON. Strips markdown fences."""
    raw = generate(prompt + "\n\nRespond with valid JSON only, no markdown.", temperature=temperature)
    # Strip markdown code fences if present
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
    return json.loads(raw)


def embed(text: str) -> list[float]:
    """Get text embedding from Gemini text-embedding-004 (768 dims)."""
    key = _get_key()
    url = f"{_BASE_URL}/text-embedding-004:embedContent?key={key}"
    payload = {
        "model": "models/text-embedding-004",
        "content": {"parts": [{"text": text[:8000]}]},  # truncate to safe limit
    }
    r = requests.post(url, json=payload, timeout=30)
    r.raise_for_status()
    return r.json()["embedding"]["values"]
