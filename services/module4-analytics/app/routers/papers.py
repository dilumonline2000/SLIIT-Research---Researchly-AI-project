"""Paper upload + quality scoring endpoint.

Accepts:
- File upload (PDF/TXT) via multipart/form-data
- Direct text submission via JSON

Returns:
- Quality scores (overall, originality, citation_impact, methodology, clarity)
- Topic classification
- Recommendations for improvement
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from ..services import quality_predictor, topic_classifier

router = APIRouter()
logger = logging.getLogger(__name__)


class PaperTextRequest(BaseModel):
    title: str = Field(..., min_length=1)
    abstract: str = Field(..., min_length=10)
    authors: Optional[list[str]] = None
    year: Optional[int] = None


class QualityAnalysisResponse(BaseModel):
    title: str
    overall_score: float
    originality_score: float
    citation_impact_score: float
    methodology_score: float
    clarity_score: float
    topic: dict  # {primary_topic, confidence, top_predictions}
    features: dict
    recommendations: list[str]
    model_info: dict


def _extract_pdf_text(content: bytes) -> tuple[str, str]:
    """Extract title (first heading) and abstract/body text from a PDF."""
    try:
        import fitz  # PyMuPDF
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

    # First non-empty line as title
    lines = [ln.strip() for ln in all_text.split("\n") if ln.strip()]
    title = lines[0][:300] if lines else "Untitled Paper"

    # Try to find abstract section
    text_lower = all_text.lower()
    abstract = ""
    for kw in ["abstract\n", "abstract:", "abstract "]:
        idx = text_lower.find(kw)
        if idx >= 0:
            start = idx + len(kw)
            # Take next 2000 chars as abstract
            abstract = all_text[start:start + 2500].strip()
            # Stop at "Introduction" or "Keywords"
            for stop_kw in ["\nintroduction", "\nkeywords", "\n1.", "\n1 "]:
                stop_idx = abstract.lower().find(stop_kw)
                if stop_idx > 100:
                    abstract = abstract[:stop_idx].strip()
                    break
            break

    if not abstract:
        # Fallback: take first 1500 chars after title
        abstract = all_text[len(title):len(title) + 1500].strip()

    return title, abstract


def _build_response(title: str, abstract: str, authors: Optional[list] = None,
                     year: Optional[int] = None) -> QualityAnalysisResponse:
    quality = quality_predictor.predict_quality(title, abstract, authors, year)
    full_text = f"{title} {abstract}"
    topic = topic_classifier.classify(full_text)

    return QualityAnalysisResponse(
        title=title,
        overall_score=quality["overall_score"],
        originality_score=quality["originality_score"],
        citation_impact_score=quality["citation_impact_score"],
        methodology_score=quality["methodology_score"],
        clarity_score=quality["clarity_score"],
        topic=topic,
        features=quality["features"],
        recommendations=quality["recommendations"],
        model_info={
            "quality_model": quality.get("model_version"),
            "topic_model": topic.get("model_version"),
        },
    )


@router.post("/papers/analyze-text", response_model=QualityAnalysisResponse)
async def analyze_paper_text(req: PaperTextRequest) -> QualityAnalysisResponse:
    """Analyze paper from direct text submission."""
    try:
        return _build_response(req.title, req.abstract, req.authors, req.year)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Paper text analysis failed")
        raise HTTPException(500, f"Analysis failed: {e}")


@router.post("/papers/upload", response_model=QualityAnalysisResponse)
async def upload_paper(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    authors: Optional[str] = Form(None),
    year: Optional[int] = Form(None),
) -> QualityAnalysisResponse:
    """Upload paper file (PDF or TXT), extract text, and analyze quality."""
    try:
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

        # Use provided title if given, else use extracted
        final_title = title or extracted_title
        author_list = [a.strip() for a in authors.split(",")] if authors else None

        if len(abstract.strip()) < 50:
            raise HTTPException(400, "Could not extract enough text from file (need >= 50 chars)")

        return _build_response(final_title, abstract, author_list, year)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Paper upload analysis failed")
        raise HTTPException(500, f"Upload analysis failed: {e}")


@router.get("/papers/health")
async def papers_health() -> dict:
    """Health check for paper analysis models."""
    return {
        "status": "ok",
        "quality_predictor": quality_predictor.get_model_info(),
        "topic_classifier": topic_classifier.get_model_info(),
    }
