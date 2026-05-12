"""Success prediction endpoint — uses trained XGBoost model on SLIIT papers.

Predicts the probability that a paper/proposal will be considered "successful"
(high quality, methodologically sound, publishable).
"""

from __future__ import annotations

import logging
import re
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from ..services import success_predictor

router = APIRouter()
logger = logging.getLogger(__name__)


class PredictTextRequest(BaseModel):
    title: str
    abstract: str
    authors: Optional[list[str]] = None
    year: Optional[int] = None


class PredictResponse(BaseModel):
    title: Optional[str] = None
    success_probability: float
    prediction: str  # "successful" or "needs_improvement"
    confidence: float
    risk_level: str  # "low", "medium", "high"
    recommendations: list[str]
    features: dict
    model_version: str


def _build_response(title: str, abstract: str, authors: Optional[list] = None,
                     year: Optional[int] = None) -> PredictResponse:
    result = success_predictor.predict_success(title, abstract, authors, year)
    return PredictResponse(
        title=title,
        success_probability=result["success_probability"],
        prediction=result["prediction"],
        confidence=result["confidence"],
        risk_level=result["risk_level"],
        recommendations=result["recommendations"],
        features=result["features"],
        model_version=result["model_version"],
    )


def _extract_pdf_text(content: bytes) -> tuple[str, str]:
    """Extract title + abstract/body from PDF."""
    try:
        import fitz
        doc = fitz.open(stream=content, filetype="pdf")
        all_text = ""
        for page in doc:
            all_text += page.get_text("text") + "\n"
        doc.close()
    except ImportError:
        raise HTTPException(500, "PyMuPDF not installed - cannot parse PDF")
    except Exception as e:
        raise HTTPException(400, f"Failed to parse PDF: {e}")

    if not all_text.strip():
        raise HTTPException(400, "PDF contains no extractable text")

    lines = [ln.strip() for ln in all_text.split("\n") if ln.strip()]

    # Skip metadata artifacts (article IDs, DOIs, short labels) to find the real title.
    # Real titles are typically >= 20 chars and don't look like identifiers.
    _META_RE = re.compile(
        r'^(article[-\s]?\d+|vol\.?\s*\d|doi:|issn|isbn|https?://|www\.|'
        r'received:|accepted:|published:|copyright|©|\d{4}[-–]\d{4}|\d+$)',
        re.IGNORECASE,
    )
    title = "Untitled"
    for line in lines[:30]:
        if len(line) < 20:
            continue
        if _META_RE.match(line):
            continue
        title = line[:300]
        break

    text_lower = all_text.lower()
    abstract = ""
    for kw in ["abstract\n", "abstract:", "abstract "]:
        idx = text_lower.find(kw)
        if idx >= 0:
            start = idx + len(kw)
            abstract = all_text[start:start + 3000].strip()
            for stop_kw in ["\nintroduction", "\nkeywords", "\n1.", "\n1 ", "\ni."]:
                stop_idx = abstract.lower().find(stop_kw)
                if stop_idx > 150:
                    abstract = abstract[:stop_idx].strip()
                    break
            break

    # If abstract wasn't found or is too short, use the paper body text.
    # Skip the first ~500 chars (header/authors/affiliations) and take the next 3500.
    if len(abstract) < 200:
        skip = min(500, len(all_text) // 4)
        abstract = all_text[skip:skip + 3500].strip()

    return title, abstract


@router.post("/predict", response_model=PredictResponse)
async def predict_success_text(req: PredictTextRequest) -> PredictResponse:
    """Predict success probability from direct text submission."""
    if not req.abstract or len(req.abstract) < 50:
        raise HTTPException(400, "Abstract must be at least 50 characters")
    return _build_response(req.title, req.abstract, req.authors, req.year)


@router.post("/predict/upload", response_model=PredictResponse)
async def predict_success_upload(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    authors: Optional[str] = Form(None),
    year: Optional[int] = Form(None),
) -> PredictResponse:
    """Predict success from uploaded paper (PDF or TXT)."""
    content = await file.read()
    if not content:
        raise HTTPException(400, "Empty file")

    filename = (file.filename or "").lower()
    if filename.endswith(".pdf"):
        extracted_title, abstract = _extract_pdf_text(content)
    elif filename.endswith((".txt", ".md")):
        text = content.decode("utf-8", errors="ignore")
        lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
        extracted_title = lines[0][:300] if lines else "Untitled"
        abstract = "\n".join(lines[1:])[:3000] if len(lines) > 1 else text[:3000]
    else:
        raise HTTPException(400, f"Unsupported file type: {filename}")

    final_title = title or extracted_title
    author_list = [a.strip() for a in authors.split(",")] if authors else None

    if len(abstract.strip()) < 50:
        raise HTTPException(400, "Could not extract enough text from file (need >= 50 chars)")

    return _build_response(final_title, abstract, author_list, year)
