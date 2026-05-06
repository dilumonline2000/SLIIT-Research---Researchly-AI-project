"""Research-gap analysis endpoints.

Endpoints
---------
  POST /gaps/analyze              – topic query → ranked gaps + trends + recommendations
  POST /gaps/analyze-pdf          – upload PDF → analyse against the corpus
  POST /gaps/analyze-full-paper   – paste full paper text → richer analysis
  POST /gaps/report               – HTML report download
  GET  /gaps/status               – local-model health
"""

from __future__ import annotations

import logging
import os
import sys
from typing import Any, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

router = APIRouter()
logger = logging.getLogger(__name__)

_services_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, _services_root)


# ─── Schemas ──────────────────────────────────────────────────────────────


class AnalyzeRequest(BaseModel):
    topic: str = Field(..., min_length=1)
    top_k: int = 8
    min_similarity: float = 0.20
    year_from: Optional[int] = None
    year_to: Optional[int] = None


class FullPaperRequest(BaseModel):
    text: str = Field(..., min_length=200)
    top_k: int = 8
    min_similarity: float = 0.20
    year_from: Optional[int] = None
    year_to: Optional[int] = None


class ReportRequest(BaseModel):
    payload: dict[str, Any]


class SupportingPaper(BaseModel):
    paper_id: str = ""
    title: str = ""
    authors: list[str] = []
    year: int | str | None = None
    url: str = ""


class ResearchGap(BaseModel):
    topic: str
    description: str
    gap_score: float
    recency_score: float
    novelty_score: float
    similarity: float = 0.0
    gap_type: str = ""
    classification: str = "general"
    category_label: str = "Gap"
    multi_dim_score: float = 0.0
    explanation: str = ""
    supporting_paper: SupportingPaper | None = None
    supporting_paper_ids: list[str] = []


class CategoryCount(BaseModel):
    category: str
    label: str
    count: int


class YearBucket(BaseModel):
    year: int
    count: int


class Trends(BaseModel):
    by_year: list[YearBucket] = []
    peak_year: int | None = None
    peak_count: int | None = None
    total_papers: int | None = None
    interpretation: str = ""


class CrossDomain(BaseModel):
    domain_a: str
    domain_b: str
    papers_in_intersection: int
    papers_in_primary: int
    opportunity_score: float
    suggestion: str


class Saturation(BaseModel):
    term: str
    paper_count: int
    warning: str


class Recommendation(BaseModel):
    title: str
    rationale: str
    problem_statement: str
    based_on: str
    supporting_paper: SupportingPaper | None = None


class AnalyzeResponse(BaseModel):
    loaded: bool
    query: str = ""
    filters: dict[str, Any] = {}
    gaps: list[ResearchGap] = []
    classification_distribution: list[CategoryCount] = []
    trends: Trends = Trends()
    saturation: list[Saturation] = []
    cross_domain: list[CrossDomain] = []
    recommendations: list[Recommendation] = []
    total_papers_analyzed: int = 0
    total_corpus_size: int = 0
    model_version: str = "unknown"
    base_model: str = "unknown"
    source: str = "local"


# ─── Helpers ──────────────────────────────────────────────────────────────


def _to_response(payload: dict[str, Any]) -> AnalyzeResponse:
    if not payload.get("loaded"):
        return AnalyzeResponse(loaded=False)

    gaps = []
    for g in payload.get("gaps", []):
        sp = g.get("supporting_paper")
        gaps.append(ResearchGap(
            topic=g.get("topic", ""),
            description=g.get("description", ""),
            gap_score=g.get("gap_score", 0.0),
            recency_score=g.get("recency_score", 0.0),
            novelty_score=g.get("novelty_score", 0.0),
            similarity=g.get("similarity", 0.0),
            gap_type=g.get("gap_type", ""),
            classification=g.get("classification", "general"),
            category_label=g.get("category_label", "Gap"),
            multi_dim_score=g.get("multi_dim_score", 0.0),
            explanation=g.get("explanation", ""),
            supporting_paper=SupportingPaper(**sp) if sp else None,
            supporting_paper_ids=[sp["paper_id"]] if sp and sp.get("paper_id") else [],
        ))

    return AnalyzeResponse(
        loaded=True,
        query=payload.get("query", ""),
        filters=payload.get("filters", {}),
        gaps=gaps,
        classification_distribution=[CategoryCount(**c) for c in payload.get("classification_distribution", [])],
        trends=Trends(**(payload.get("trends") or {})),
        saturation=[Saturation(**s) for s in payload.get("saturation", [])],
        cross_domain=[CrossDomain(**c) for c in payload.get("cross_domain", [])],
        recommendations=[Recommendation(
            title=r["title"], rationale=r["rationale"],
            problem_statement=r["problem_statement"], based_on=r["based_on"],
            supporting_paper=SupportingPaper(**r["supporting_paper"]) if r.get("supporting_paper") else None,
        ) for r in payload.get("recommendations", [])],
        total_papers_analyzed=payload.get("total_papers_analyzed", 0),
        total_corpus_size=payload.get("total_corpus_size", 0),
        model_version=payload.get("model_version", "unknown"),
        base_model=payload.get("base_model", "unknown"),
        source="local",
    )


# ─── Endpoints ────────────────────────────────────────────────────────────


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    """Topic-aware gap analysis with the full intelligence layer."""
    try:
        from app.services import gap_intelligence
        payload = gap_intelligence.analyze(
            req.topic,
            top_k=req.top_k,
            min_similarity=req.min_similarity,
            year_from=req.year_from,
            year_to=req.year_to,
        )
        return _to_response(payload)
    except Exception as e:
        logger.warning("Gap analysis failed: %s", e)
        return AnalyzeResponse(loaded=False)


@router.post("/analyze-pdf", response_model=AnalyzeResponse)
async def analyze_pdf(
    file: UploadFile = File(..., description="PDF research paper"),
    top_k: int = Form(8),
    min_similarity: float = Form(0.20),
    year_from: Optional[int] = Form(None),
    year_to: Optional[int] = Form(None),
) -> AnalyzeResponse:
    """Upload a PDF, extract its full text + section breakdown, and analyse."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted (.pdf)")

    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    if len(pdf_bytes) > 25 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="PDF too large (max 25 MB)")

    try:
        from app.services import pdf_extractor, gap_intelligence
        ext = pdf_extractor.extract_text(pdf_bytes)
        if len(ext["text"]) < 100:
            raise HTTPException(status_code=422, detail=ext.get("warning") or "PDF text too short to analyse.")

        sections = pdf_extractor.split_paper_sections(ext["text"])
        # Build a focused query: title-ish opening + abstract + methodology emphasis
        query_parts: list[str] = []
        if sections["abstract"]:
            query_parts.append(sections["abstract"][:1500])
        else:
            query_parts.append(ext["text"][:1500])
        if sections["methodology"]:
            query_parts.append(sections["methodology"][:1000])
        if sections["conclusion"]:
            query_parts.append(sections["conclusion"][:800])
        query = " ".join(query_parts)

        payload = gap_intelligence.analyze(
            query, top_k=top_k, min_similarity=min_similarity,
            year_from=year_from, year_to=year_to,
        )
        # Decorate with file info
        payload["query"] = f"PDF: {file.filename}"
        return _to_response(payload)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("PDF analysis failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Could not analyse the PDF: {e}")


@router.post("/analyze-full-paper", response_model=AnalyzeResponse)
async def analyze_full_paper(req: FullPaperRequest) -> AnalyzeResponse:
    """Pasted full paper text — splits into sections, then analyses."""
    try:
        from app.services import pdf_extractor, gap_intelligence
        sections = pdf_extractor.split_paper_sections(req.text)
        query_parts: list[str] = []
        if sections["abstract"]:
            query_parts.append(sections["abstract"][:1500])
        else:
            query_parts.append(req.text[:1500])
        if sections["methodology"]:
            query_parts.append(sections["methodology"][:1000])
        if sections["conclusion"]:
            query_parts.append(sections["conclusion"][:800])

        payload = gap_intelligence.analyze(
            " ".join(query_parts),
            top_k=req.top_k, min_similarity=req.min_similarity,
            year_from=req.year_from, year_to=req.year_to,
        )
        return _to_response(payload)
    except Exception as e:
        logger.exception("Full-paper analysis failed: %s", e)
        return AnalyzeResponse(loaded=False)


@router.post("/report", response_class=HTMLResponse)
async def report(req: ReportRequest) -> HTMLResponse:
    """Render a structured gap-analysis report as standalone HTML."""
    from app.services import gap_intelligence
    html = gap_intelligence.generate_report_html(req.payload)
    return HTMLResponse(content=html)


@router.get("/status")
async def gap_analyzer_status() -> dict:
    try:
        from app.services import gap_analyzer
        return gap_analyzer.get_model_info()
    except Exception as e:
        return {"loaded": False, "error": str(e)}
