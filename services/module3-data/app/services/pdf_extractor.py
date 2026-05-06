"""PDF text extractor with two-tier fallback.

Many academic PDFs (especially IEEE/ACM-style two-column layouts) have CMap-
encoded fonts that `pypdf` extracts as garbage or empty strings. `pdfplumber`
handles these much better at the cost of a slower import.

Strategy:
  1. Try `pypdf` first — fastest, works for ~70% of PDFs.
  2. If it produced < FALLBACK_THRESHOLD characters, retry with `pdfplumber`.
  3. Return whichever produced more text. If both fail, return ''.

Public API:
    extract_text(pdf_bytes: bytes, max_pages: int = 30) -> dict
        returns {
          "text": str,
          "n_pages": int,
          "engine": "pypdf" | "pdfplumber" | "none",
          "warning": str | None,
        }
"""

from __future__ import annotations

import io
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_MAX_PAGES = 30
FALLBACK_THRESHOLD = 200  # if pypdf gives less, try pdfplumber


def _clean(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"-\n", "", text)         # word-\nbreak  →  wordbreak
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def _try_pypdf(pdf_bytes: bytes, max_pages: int) -> tuple[str, int]:
    """Returns (text, n_pages_extracted)."""
    try:
        from pypdf import PdfReader
    except ImportError:
        return "", 0
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
    except Exception as e:
        logger.warning("[pdf_extractor] pypdf open failed: %s", e)
        return "", 0
    n = min(len(reader.pages), max_pages)
    pages_out: list[str] = []
    for i in range(n):
        try:
            page_text = reader.pages[i].extract_text() or ""
        except Exception as e:
            logger.debug("[pdf_extractor] pypdf page %d failed: %s", i, e)
            continue
        if page_text.strip():
            pages_out.append(page_text)
    return _clean("\n\n".join(pages_out)), n


def _try_pdfplumber(pdf_bytes: bytes, max_pages: int) -> tuple[str, int]:
    try:
        import pdfplumber
    except ImportError:
        return "", 0
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            n = min(len(pdf.pages), max_pages)
            pages_out: list[str] = []
            for i in range(n):
                try:
                    page_text = pdf.pages[i].extract_text() or ""
                except Exception as e:
                    logger.debug("[pdf_extractor] pdfplumber page %d failed: %s", i, e)
                    continue
                if page_text.strip():
                    pages_out.append(page_text)
        return _clean("\n\n".join(pages_out)), n
    except Exception as e:
        logger.warning("[pdf_extractor] pdfplumber open failed: %s", e)
        return "", 0


def extract_text(pdf_bytes: bytes, max_pages: int = DEFAULT_MAX_PAGES) -> dict[str, Any]:
    """Extract text using pypdf, falling back to pdfplumber if needed."""
    result: dict[str, Any] = {"text": "", "n_pages": 0, "engine": "none", "warning": None}
    if not pdf_bytes:
        result["warning"] = "Empty file"
        return result

    # Tier 1: pypdf (fast)
    text_a, n_a = _try_pypdf(pdf_bytes, max_pages)

    # Tier 2: pdfplumber (slower but handles CMap fonts)
    text_b, n_b = "", 0
    if len(text_a) < FALLBACK_THRESHOLD:
        text_b, n_b = _try_pdfplumber(pdf_bytes, max_pages)

    # Pick whichever extracted more text
    if len(text_b) > len(text_a):
        result["text"] = text_b
        result["n_pages"] = n_b
        result["engine"] = "pdfplumber"
        if len(text_a) > 0:
            result["warning"] = f"pypdf only got {len(text_a)} chars; pdfplumber recovered {len(text_b)}"
    elif len(text_a) > 0:
        result["text"] = text_a
        result["n_pages"] = n_a
        result["engine"] = "pypdf"

    if not result["text"]:
        result["warning"] = (
            "Both pypdf and pdfplumber returned empty text. "
            "The PDF is likely a scanned image without OCR — "
            "run an OCR tool (e.g. Tesseract / Adobe Acrobat OCR) and re-upload."
        )

    return result
