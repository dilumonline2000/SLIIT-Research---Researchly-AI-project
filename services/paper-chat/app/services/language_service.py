"""Language detection + translation + Singlish handling.

Lightweight, dependency-tolerant: works without any heavy translation models.
Optional: if Helsinki-NLP/opus-mt is available, uses it for SI/TA translation.
Falls back to identity translation otherwise so the chat flow never breaks.
"""

from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Tuple

# Sinhala U+0D80..U+0DFF, Tamil U+0B80..U+0BFF
_SINHALA_RE = re.compile(r"[\u0D80-\u0DFF]")
_TAMIL_RE = re.compile(r"[\u0B80-\u0BFF]")

# Built-in default Singlish dictionary (Romanized Sinhala fragments).
# Override / extend by setting SINGLISH_DICT_PATH to a JSON file.
_DEFAULT_SINGLISH_DICT = {
    "eka": "the",
    "meka": "this",
    "oya": "that",
    "da": "?",
    "ද": "?",
    "gana": "about",
    "kiyanna": "tell",
    "kiyanawa": "say",
    "hodai": "good",
    "hodayi": "good",
    "karanawa": "do",
    "karanna": "do",
    "mokakda": "what",
    "mokada": "what",
    "kohomada": "how",
    "aye": "why",
    "tiyenawa": "exists",
    "danna": "know",
    "danne": "know",
    "banna": "cannot",
    "puluwan": "can",
    "kenek": "person",
    "walata": "for",
    "wala": "of",
    "ekak": "one",
    "research": "research",
    "paper": "paper",
    "supervisor": "supervisor",
}

_SINGLISH_TRIGGERS = {
    "eka", "meka", "oya", "gana", "kiyanna", "karanawa", "karanna",
    "mokakda", "kohomada", "tiyenawa", "puluwan", "kenek",
}


@lru_cache(maxsize=1)
def _load_singlish_dict() -> dict:
    path = os.environ.get("SINGLISH_DICT_PATH")
    if path and Path(path).exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                user = json.load(f)
            return {**_DEFAULT_SINGLISH_DICT, **user}
        except Exception:
            pass
    return dict(_DEFAULT_SINGLISH_DICT)


def detect_language(text: str) -> Tuple[str, float, bool]:
    """Returns (language_code, confidence, is_singlish).

    Order: Sinhala unicode > Tamil unicode > Singlish trigger > langdetect > 'en'.
    """
    if not text or not text.strip():
        return "en", 1.0, False

    if _SINHALA_RE.search(text):
        return "si", 1.0, False
    if _TAMIL_RE.search(text):
        return "ta", 1.0, False

    lower_tokens = set(re.findall(r"[a-zA-Z']+", text.lower()))
    if lower_tokens & _SINGLISH_TRIGGERS:
        return "singlish", 0.9, True

    try:
        from langdetect import detect, DetectorFactory

        DetectorFactory.seed = 0
        code = detect(text)
        return code, 0.7, False
    except Exception:
        return "en", 0.5, False


def singlish_to_english(text: str) -> str:
    """Best-effort token-level transliteration."""
    mapping = _load_singlish_dict()
    out = []
    for tok in re.findall(r"\S+|\s+", text):
        if tok.isspace():
            out.append(tok)
            continue
        bare = re.sub(r"[^\w]", "", tok).lower()
        out.append(mapping.get(bare, tok))
    return "".join(out)


def normalise_query(text: str) -> Tuple[str, str, bool]:
    """Detect language and return an English query suitable for embedding.

    Returns (english_query, detected_language, is_singlish).
    """
    lang, _conf, is_singlish = detect_language(text)
    if is_singlish:
        return singlish_to_english(text), "singlish", True
    if lang == "si" or lang == "ta":
        return translate(text, source=lang, target="en"), lang, False
    return text, lang, False


def translate(text: str, source: str = "auto", target: str = "en") -> str:
    """Translate text. Falls back to identity if no translation backend is available."""
    if not text:
        return text
    if source == target:
        return text
    # Optional: try Helsinki-NLP MarianMT if installed
    try:
        from transformers import MarianMTModel, MarianTokenizer  # type: ignore

        pair = f"{source}-{target}" if source != "auto" else f"en-{target}"
        model_name = f"Helsinki-NLP/opus-mt-{pair}"
        tokenizer = MarianTokenizer.from_pretrained(model_name)
        model = MarianMTModel.from_pretrained(model_name)
        batch = tokenizer([text], return_tensors="pt", padding=True, truncation=True)
        gen = model.generate(**batch, max_length=512)
        return tokenizer.decode(gen[0], skip_special_tokens=True)
    except Exception:
        # Graceful fallback: return original text
        return text
