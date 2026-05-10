"""Research-paper summarizer endpoint.

Primary path: local extractive summarizer (SBERT centroid + lead-bias + MMR
              + section-aware categorisation).
Fallback path: Gemini abstractive prompt.

Two entry points share the same backend pipeline:
  POST /summarize          – body {text, length}
  POST /summarize/upload   – multipart {file: PDF, length, paper_id?}
"""

from __future__ import annotations

import logging
import os
import sys
from typing import Literal, Optional

from datetime import datetime
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

router = APIRouter()
logger = logging.getLogger(__name__)

_services_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, _services_root)

LengthLiteral = Literal["quick", "short", "standard", "medium", "detailed", "extensive"]

LENGTH_INSTRUCTIONS = {
    "quick":     "Write 4-5 concise bullet points capturing only the most essential findings.",
    "short":     "Write 4-5 concise bullet points capturing only the most essential findings.",
    "standard":  "Write 8-10 detailed bullet points covering background, objective, methodology, results, and conclusion.",
    "medium":    "Write 8-10 detailed bullet points covering background, objective, methodology, results, and conclusion.",
    "detailed":  "Write 12-15 in-depth bullet points covering every section: background, objective, methodology, datasets, results, limitations, and conclusion.",
    "extensive": "Write 18-20 comprehensive bullet points fully covering background, motivation, objective, methodology, datasets, experiments, results, comparisons, limitations, and conclusion.",
}


class SummarizeRequest(BaseModel):
    text: str = Field(..., min_length=100)
    length: LengthLiteral = "standard"
    paper_id: Optional[str] = None


class KeyPoint(BaseModel):
    category: str
    category_label: str
    text: str


class SummarizeResponse(BaseModel):
    summary: str
    sentences: list[str] = []
    key_points: list[KeyPoint] = []
    grouped_points: dict[str, list[KeyPoint]] = {}
    n_sentences_input: int = 0
    n_sentences_output: int = 0
    compression_ratio: float = 0.0
    model_version: str
    source: str = "unknown"
    rouge_scores: dict[str, float] | None = None
    filename: Optional[str] = None
    pdf_text_length: Optional[int] = None


def _persist_summary(paper_id: str, summary: str, length: str, model_version: str) -> None:
    try:
        from shared.supabase_client import get_supabase_admin
        sb = get_supabase_admin()
        sb.table("research_summaries").upsert({
            "paper_id": paper_id,
            "summary": summary,
            "summary_type": length,
            "model_version": model_version,
        }).execute()
    except Exception as e:
        logger.warning("Failed to store summary: %s", e)


def _build_response_from_local(result: dict, *, length: str, source: str = "local",
                                filename: Optional[str] = None,
                                pdf_text_length: Optional[int] = None) -> SummarizeResponse:
    return SummarizeResponse(
        summary=result["summary"],
        sentences=result.get("sentences", []),
        key_points=[KeyPoint(**kp) for kp in result.get("key_points", [])],
        grouped_points={
            k: [KeyPoint(**kp) for kp in v]
            for k, v in result.get("grouped_points", {}).items()
        },
        n_sentences_input=result.get("n_sentences_input", 0),
        n_sentences_output=result.get("n_sentences_output", 0),
        compression_ratio=result.get("compression_ratio", 0.0),
        model_version=f"local-extractive-{result.get('model_version','1.0.0')}",
        source=source,
        filename=filename,
        pdf_text_length=pdf_text_length,
    )


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize(req: SummarizeRequest) -> SummarizeResponse:
    """Generate a point-wise summary, preferring the local extractive model."""

    # ── 1. Local extractive summarizer ───────────────────────────────────────
    try:
        from app.services import extractive_summarizer

        result = extractive_summarizer.summarize(req.text, length=req.length)
        if result.get("loaded") and result.get("summary"):
            if req.paper_id:
                _persist_summary(req.paper_id, result["summary"], req.length,
                                 f"local-extractive-{result.get('model_version','1.0.0')}")
            return _build_response_from_local(result, length=req.length)
    except Exception as e:
        logger.warning("Local summarizer failed: %s — falling back to Gemini", e)

    # ── 2. Gemini fallback ───────────────────────────────────────────────────
    try:
        from shared.gemini_client import generate

        instruction = LENGTH_INSTRUCTIONS[req.length]
        prompt = f"""You are an expert academic summarizer. {instruction}

Research text:
{req.text[:8000]}

Output as plain text bullet points (one per line, prefixed with "• "). No preamble, no labels."""
        summary = generate(prompt, temperature=0.3, max_tokens=1024)
        if req.paper_id and summary:
            _persist_summary(req.paper_id, summary, req.length, "gemini-2.5-flash")
        return SummarizeResponse(summary=summary, model_version="gemini-2.5-flash", source="gemini")
    except Exception as e:
        logger.error("Gemini summarization also failed: %s", e)

    return SummarizeResponse(summary="", model_version="fallback", source="fallback")


@router.post("/summarize/upload", response_model=SummarizeResponse)
async def summarize_upload(
    file: UploadFile = File(..., description="PDF research paper"),
    length: str = Form("standard"),
    paper_id: Optional[str] = Form(None),
) -> SummarizeResponse:
    """Extract text from an uploaded PDF and summarize it.

    Accepts: multipart/form-data with `file` (PDF), `length`, optional `paper_id`.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted (.pdf)")

    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    if len(pdf_bytes) > 25 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="PDF too large (max 25 MB)")

    # Validate length value (accept loose strings to be tolerant of frontends)
    length_norm = (length or "standard").strip().lower()
    if length_norm not in LENGTH_INSTRUCTIONS:
        length_norm = "standard"

    # Extract text (pypdf first → pdfplumber fallback)
    try:
        from app.services import pdf_extractor
        ext = pdf_extractor.extract_text(pdf_bytes)
        text = ext["text"]
    except Exception as e:
        logger.error("PDF extraction failed: %s", e)
        raise HTTPException(status_code=422, detail=f"Could not extract text from PDF: {e}")

    logger.info("[summarize/upload] %s: %d pages, %d chars (engine=%s)",
                file.filename, ext.get("n_pages", 0), len(text), ext.get("engine"))

    if len(text) < 100:
        warn = ext.get("warning") or (
            "PDF text too short to summarize (extracted only "
            f"{len(text)} characters from {ext.get('n_pages', 0)} pages). "
            "The PDF is likely image-only — run OCR and re-upload."
        )
        raise HTTPException(status_code=422, detail=warn)

    try:
        from app.services import extractive_summarizer

        result = extractive_summarizer.summarize(text, length=length_norm)
        if result.get("loaded") and result.get("summary"):
            if paper_id:
                _persist_summary(paper_id, result["summary"], length_norm,
                                 f"local-extractive-{result.get('model_version','1.0.0')}")
            return _build_response_from_local(
                result, length=length_norm, filename=file.filename, pdf_text_length=len(text),
            )
    except Exception as e:
        logger.error("Local summarization on uploaded PDF failed: %s", e)

    return SummarizeResponse(
        summary="",
        model_version="fallback",
        source="fallback",
        filename=file.filename,
        pdf_text_length=len(text),
    )


class ReportRequest(BaseModel):
    summary: str = ""
    key_points: list[KeyPoint] = []
    grouped_points: dict[str, list[KeyPoint]] = {}
    sentences: list[str] = []
    n_sentences_input: int = 0
    n_sentences_output: int = 0
    compression_ratio: float = 0.0
    model_version: str = "unknown"
    source: str = "unknown"
    filename: Optional[str] = None
    pdf_text_length: Optional[int] = None
    title: Optional[str] = None  # optional human title for the report header


_CATEGORY_BG = {
    "background":  "#e2e8f0",
    "objective":   "#dbeafe",
    "methodology": "#dbeafe",
    "results":     "#d1fae5",
    "limitations": "#fef3c7",
    "conclusion":  "#ede9fe",
    "general":     "#f3f4f6",
}


def _esc(s: Any) -> str:
    return (str(s) if s is not None else "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


@router.post("/summarize/report", response_class=HTMLResponse)
async def summarize_report(req: ReportRequest) -> HTMLResponse:
    """Render a previously-generated summary as a styled, downloadable HTML page.

    The frontend calls this with the same SummarizeResponse it just received,
    so no re-computation happens server-side.
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    title = _esc(req.title or req.filename or "Research Paper Summary")

    grouped_html = ""
    if req.grouped_points:
        for cat, points in req.grouped_points.items():
            if not points:
                continue
            label = points[0].category_label if points else cat.title()
            bg = _CATEGORY_BG.get(cat, "#f3f4f6")
            items = "".join(f"<li>{_esc(p.text)}</li>" for p in points)
            grouped_html += (
                f'<section style="background:{bg};border-radius:6px;padding:.75rem 1rem;margin:.6rem 0;">'
                f'<h3 style="margin:.2rem 0;color:#312e81">{_esc(label)}'
                f' <span style="font-size:.75rem;color:#6b7280">({len(points)} points)</span></h3>'
                f'<ul style="margin:.4rem 0 0 1.2rem">{items}</ul></section>'
            )
    elif req.summary:
        grouped_html = (
            f'<section style="background:#f3f4f6;border-radius:6px;padding:.75rem 1rem;margin:.6rem 0;">'
            f'<p>{_esc(req.summary)}</p></section>'
        )

    meta_chips = []
    if req.filename:
        meta_chips.append(f"📄 {_esc(req.filename)}")
    if req.pdf_text_length:
        meta_chips.append(f"{req.pdf_text_length:,} chars extracted")
    if req.n_sentences_input:
        meta_chips.append(
            f"{req.n_sentences_input} → {req.n_sentences_output} sentences "
            f"({(req.compression_ratio * 100):.0f}% of original)"
        )
    if req.source:
        meta_chips.append(f"source: {_esc(req.source)}")
    meta_html = " · ".join(meta_chips)

    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8" />
<title>{title}</title>
<style>
  body {{ font-family: Georgia, 'Times New Roman', serif; max-width: 880px; margin: 2rem auto; padding: 0 1.5rem; color: #1f2937; line-height: 1.6; }}
  h1 {{ color: #312e81; border-bottom: 3px solid #6366f1; padding-bottom: .5rem; }}
  .meta {{ color: #4b5563; font-size: .85rem; margin-bottom: 1.5rem; }}
  ul {{ padding-left: 1.25rem; margin: .35rem 0; }}
  li {{ margin: .25rem 0; }}
  .footer {{ margin-top: 3rem; color: #9ca3af; font-size: .75rem; border-top: 1px solid #e5e7eb; padding-top: .75rem; }}
</style></head><body>
  <h1>{title}</h1>
  <p class="meta">Generated {now}{f' · {meta_html}' if meta_html else ''}</p>

  {grouped_html or '<p>No summary content.</p>'}

  <p class="footer">Researchly AI · Module 3 (Data Management) · model: {_esc(req.model_version)}</p>
</body></html>"""

    return HTMLResponse(content=html)


@router.get("/summarize/status")
async def summarize_status() -> dict:
    try:
        from app.services import extractive_summarizer
        return extractive_summarizer.get_model_info()
    except Exception as e:
        return {"loaded": False, "error": str(e)}
