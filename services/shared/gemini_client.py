"""Shared Gemini client used by all 5 Python services."""

import os
import json
import requests
from typing import Optional

_API_KEY: Optional[str] = None
_MODEL: str = "gemini-2.5-flash"
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
    """Call Gemini generateContent and return the text response."""
    key = _get_key()
    model = _get_model()
    url = f"{_BASE_URL}/{model}:generateContent?key={key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        },
    }
    r = requests.post(url, json=payload, timeout=60)
    r.raise_for_status()
    data = r.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except (KeyError, IndexError) as e:
        raise RuntimeError(f"Unexpected Gemini response: {data}") from e


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
