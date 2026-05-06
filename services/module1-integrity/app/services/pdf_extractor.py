"""PDF text extractor for the Gap Analyzer's PDF-upload flow.

Same two-tier strategy used by module 3's summarizer:
  1. pypdf (fast, ~70 % of academic PDFs)
  2. pdfplumber (handles CMap-encoded fonts in IEEE/ACM-style two-column layouts)

Public API:
    extract_text(pdf_bytes: bytes, max_pages: int = 30) -> dict
"""

from __future__ import annotations

import io
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_MAX_PAGES = 30
FALLBACK_THRESHOLD = 200


def _clean(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"-\n", "", text)
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def _try_pypdf(pdf_bytes: bytes, max_pages: int) -> tuple[str, int]:
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
    out: list[str] = []
    for i in range(n):
        try:
            t = reader.pages[i].extract_text() or ""
        except Exception:
            continue
        if t.strip():
            out.append(t)
    return _clean("\n\n".join(out)), n


def _try_pdfplumber(pdf_bytes: bytes, max_pages: int) -> tuple[str, int]:
    try:
        import pdfplumber
    except ImportError:
        return "", 0
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            n = min(len(pdf.pages), max_pages)
            out: list[str] = []
            for i in range(n):
                try:
                    t = pdf.pages[i].extract_text() or ""
                except Exception:
                    continue
                if t.strip():
                    out.append(t)
        return _clean("\n\n".join(out)), n
    except Exception as e:
        logger.warning("[pdf_extractor] pdfplumber open failed: %s", e)
        return "", 0


def extract_text(pdf_bytes: bytes, max_pages: int = DEFAULT_MAX_PAGES) -> dict[str, Any]:
    result: dict[str, Any] = {"text": "", "n_pages": 0, "engine": "none", "warning": None}
    if not pdf_bytes:
        result["warning"] = "Empty file"
        return result

    text_a, n_a = _try_pypdf(pdf_bytes, max_pages)
    text_b, n_b = ("", 0)
    if len(text_a) < FALLBACK_THRESHOLD:
        text_b, n_b = _try_pdfplumber(pdf_bytes, max_pages)

    if len(text_b) > len(text_a):
        result.update(text=text_b, n_pages=n_b, engine="pdfplumber")
        if len(text_a) > 0:
            result["warning"] = f"pypdf only got {len(text_a)} chars; pdfplumber recovered {len(text_b)}"
    elif len(text_a) > 0:
        result.update(text=text_a, n_pages=n_a, engine="pypdf")

    if not result["text"]:
        result["warning"] = (
            "Both pypdf and pdfplumber returned empty text. The PDF is likely a scanned "
            "image without OCR — run an OCR tool (Tesseract / Adobe Acrobat OCR) and re-upload."
        )

    return result


def split_paper_sections(text: str) -> dict[str, str]:
    """Heuristically split a research paper's full text into core sections.

    Returns a dict with keys: abstract, introduction, methodology, results, conclusion, full.
    Missing sections come back as empty strings.
    """
    if not text:
        return {"abstract": "", "introduction": "", "methodology": "", "results": "", "conclusion": "", "full": ""}

    sections = {
        "abstract":     [r"\babstract\b"],
        "introduction": [r"\b1\.?\s*introduction\b", r"\bintroduction\b"],
        "methodology":  [r"\bmethodolog\w*\b", r"\bmaterials?\s+and\s+methods?\b", r"\bmethods?\b"],
        "results":      [r"\bresults?\b", r"\bfindings\b", r"\bevaluation\b"],
        "conclusion":   [r"\bconclusion\b", r"\bdiscussion\b", r"\bsummary\b"],
    }

    # Find the first match position for each section header
    positions: list[tuple[str, int]] = []
    lower = text.lower()
    for key, patterns in sections.items():
        first = -1
        for p in patterns:
            m = re.search(p, lower)
            if m and (first == -1 or m.start() < first):
                first = m.start()
        if first != -1:
            positions.append((key, first))

    positions.sort(key=lambda x: x[1])
    out = {key: "" for key in sections}
    out["full"] = text

    for i, (key, start) in enumerate(positions):
        end = positions[i + 1][1] if i + 1 < len(positions) else len(text)
        out[key] = text[start:end].strip()[:8000]

    return out
