"""Plagiarism trends + paper comparison.

Endpoints
---------
  GET  /plagiarism-trends                  — legacy: pull rows from Supabase
  POST /plagiarism-trends/search           — topic-aware retrieval (with related papers)
  POST /plagiarism-trends/search/report    — search-result HTML report download
  POST /plagiarism-trends/compare          — compare two paper texts
  POST /plagiarism-trends/compare-pdf      — compare two uploaded PDFs (multipart)
  POST /plagiarism-trends/compare/report   — comparison HTML report download
  GET  /plagiarism-trends/status           — model health
"""

from __future__ import annotations

import logging
import os
import sys
from collections import defaultdict
from typing import Any, Optional

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

router = APIRouter()
logger = logging.getLogger(__name__)

_services_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, _services_root)


# ─── Schemas ─────────────────────────────────────────────────────────────────


class TrendEntry(BaseModel):
    cohort_year: int
    topic_area: str
    avg_similarity: float
    max_similarity: float
    trend_direction: str


class TrendsResponse(BaseModel):
    trends: list[TrendEntry]
    source: str = "supabase"


class TopicSearchRequest(BaseModel):
    topic: str = Field(..., min_length=1)
    top_k: int = 5
    min_topic_similarity: float = 0.25
    related_papers_top_k: int = 6


class RelatedPaper(BaseModel):
    paper_id: str = ""
    title: str = ""
    authors: list[str] = []
    year: int | str | None = None
    url: str = ""
    subject: str | list[str] | None = None
    similarity: float = 0.0
    abstract_excerpt: str = ""


class PaperRef(BaseModel):
    paper_id: str = ""
    title: str = ""
    url: str = ""


class FlaggedPair(BaseModel):
    similarity: float
    paper_a: PaperRef
    paper_b: PaperRef


class YearlyTrend(BaseModel):
    topic: str
    year: int
    n_papers: int
    avg_similarity: float
    max_similarity: float
    p95_similarity: float
    n_high_similarity_pairs: int
    trend_direction: str
    top_pairs: list[FlaggedPair] = []


class TopicMatch(BaseModel):
    topic: str
    similarity: float
    n_records: int
    n_papers_total: int
    avg_similarity_overall: float
    max_avg_similarity: float
    n_high_similarity_pairs_total: int
    latest_year: int
    latest_trend_direction: str
    yearly: list[YearlyTrend] = []


class TopicSearchResponse(BaseModel):
    matches: list[TopicMatch]
    related_papers: list[RelatedPaper] = []
    query: str = ""
    total_topics: int = 0
    model_version: str = ""
    base_model: str = ""
    source: str = "local"


class ComparePapersRequest(BaseModel):
    text_a: str = Field(..., min_length=20)
    text_b: str = Field(..., min_length=20)
    title_a: str = ""
    title_b: str = ""
    top_pairs: int = 5


class FlaggedSentencePair(BaseModel):
    similarity: float
    sentence_a: str
    sentence_b: str
    index_a: int
    index_b: int


class CompareResponse(BaseModel):
    document_similarity: float
    ngram_jaccard: float
    ngram_overlap_in_a: float
    ngram_overlap_in_b: float
    risk_score: float
    risk_level: str  # minimal | low | medium | high
    flagged_pairs: list[FlaggedSentencePair] = []
    n_sentences_a: int = 0
    n_sentences_b: int = 0
    title_a: str = ""
    title_b: str = ""
    model_version: str = ""
    source: str = "local"


# ─── Endpoints ───────────────────────────────────────────────────────────────


@router.get("/plagiarism-trends", response_model=TrendsResponse)
async def get_trends(
    year_from: int = Query(2020, description="Start year"),
    year_to: int = Query(2026, description="End year"),
) -> TrendsResponse:
    """Aggregate rows from the `plagiarism_trends` Supabase table (legacy).

    Prefer `POST /plagiarism-trends/search` for topic-aware retrieval over the
    locally-trained corpus.
    """
    try:
        from shared.supabase_client import get_supabase_admin
    except ImportError:
        return TrendsResponse(trends=[])

    try:
        sb = get_supabase_admin()
        result = (
            sb.table("plagiarism_trends")
            .select("*")
            .gte("cohort_year", year_from)
            .lte("cohort_year", year_to)
            .order("cohort_year")
            .execute()
        )
        rows = result.data or []
    except Exception as e:
        logger.warning("Failed to fetch plagiarism trends: %s", e)
        rows = []

    if not rows:
        # Synthesise from the local corpus when Supabase is empty
        try:
            from app.services import plagiarism_analyzer
            info = plagiarism_analyzer.search_trends("research", top_k=12)
            entries: list[TrendEntry] = []
            for m in info.get("matches", []):
                for y in m.get("yearly", []):
                    if year_from <= int(y["year"]) <= year_to:
                        entries.append(TrendEntry(
                            cohort_year=int(y["year"]),
                            topic_area=str(y["topic"])[:60],
                            avg_similarity=float(y["avg_similarity"]),
                            max_similarity=float(y["max_similarity"]),
                            trend_direction=str(y["trend_direction"]),
                        ))
            return TrendsResponse(trends=entries[:50], source="local-corpus")
        except Exception as e:
            logger.warning("Local-corpus fallback failed: %s", e)
            return TrendsResponse(trends=[])

    # Aggregate by (year, topic)
    grouped: dict[tuple, list] = defaultdict(list)
    for row in rows:
        key = (row.get("cohort_year", 0), row.get("topic_area", "unknown"))
        grouped[key].append(float(row.get("similarity_score", 0)))

    topic_year_avg: dict[str, dict[int, float]] = defaultdict(dict)
    trends: list[TrendEntry] = []
    for (year, topic), scores in sorted(grouped.items()):
        avg_sim = sum(scores) / len(scores)
        max_sim = max(scores)
        topic_year_avg[topic][year] = avg_sim

        prev_avg = topic_year_avg[topic].get(year - 1)
        if prev_avg is None:
            direction = "baseline"
        elif avg_sim > prev_avg + 0.02:
            direction = "increasing"
        elif avg_sim < prev_avg - 0.02:
            direction = "decreasing"
        else:
            direction = "stable"

        trends.append(TrendEntry(
            cohort_year=year, topic_area=topic,
            avg_similarity=round(avg_sim, 4),
            max_similarity=round(max_sim, 4),
            trend_direction=direction,
        ))
    return TrendsResponse(trends=trends, source="supabase")


def _do_search(req: TopicSearchRequest) -> dict[str, Any]:
    from app.services import plagiarism_analyzer
    return plagiarism_analyzer.search_trends(
        req.topic,
        top_k=req.top_k,
        min_topic_similarity=req.min_topic_similarity,
        include_related_papers=True,
        related_papers_top_k=req.related_papers_top_k,
    )


@router.post("/plagiarism-trends/search", response_model=TopicSearchResponse)
async def search_topic_trends(req: TopicSearchRequest) -> TopicSearchResponse:
    """Topic search: returns matched trend buckets + actual related SLIIT papers."""
    try:
        result = _do_search(req)
        if not result.get("loaded"):
            return TopicSearchResponse(matches=[], query=req.topic, source="fallback")
        return TopicSearchResponse(
            matches=[TopicMatch(**m) for m in result.get("matches", [])],
            related_papers=[RelatedPaper(**p) for p in result.get("related_papers", [])],
            query=req.topic,
            total_topics=result.get("total_topics", 0),
            model_version=result.get("model_version", "unknown"),
            base_model=result.get("base_model", "unknown"),
            source="local",
        )
    except Exception as e:
        logger.error("Local trend search failed: %s", e)
        return TopicSearchResponse(matches=[], query=req.topic, source="fallback")


@router.post("/plagiarism-trends/search/report", response_class=HTMLResponse)
async def search_report(req: TopicSearchRequest) -> HTMLResponse:
    """Render the topic-search result as a downloadable HTML report."""
    from app.services import plagiarism_analyzer
    result = _do_search(req)
    payload = {
        "query": req.topic,
        "matches": result.get("matches", []),
        "related_papers": result.get("related_papers", []),
    }
    return HTMLResponse(content=plagiarism_analyzer.generate_search_report_html(payload))


@router.post("/plagiarism-trends/compare", response_model=CompareResponse)
async def compare_two_papers(req: ComparePapersRequest) -> CompareResponse:
    """Pairwise plagiarism analysis of two arbitrary paper texts."""
    try:
        from app.services import plagiarism_analyzer

        result = plagiarism_analyzer.compare_papers(req.text_a, req.text_b, top_pairs=req.top_pairs)
        if not result.get("loaded"):
            raise RuntimeError("Local plagiarism analyzer not available")
        return CompareResponse(
            document_similarity=result["document_similarity"],
            ngram_jaccard=result["ngram_jaccard"],
            ngram_overlap_in_a=result["ngram_overlap_in_a"],
            ngram_overlap_in_b=result["ngram_overlap_in_b"],
            risk_score=result["risk_score"],
            risk_level=result["risk_level"],
            flagged_pairs=[FlaggedSentencePair(**p) for p in result.get("flagged_pairs", [])],
            n_sentences_a=result.get("n_sentences_a", 0),
            n_sentences_b=result.get("n_sentences_b", 0),
            title_a=req.title_a,
            title_b=req.title_b,
            model_version=result.get("model_version", "unknown"),
            source="local",
        )
    except Exception as e:
        logger.error("Pair comparison failed: %s", e)
        return CompareResponse(
            document_similarity=0.0, ngram_jaccard=0.0,
            ngram_overlap_in_a=0.0, ngram_overlap_in_b=0.0,
            risk_score=0.0, risk_level="minimal",
            title_a=req.title_a, title_b=req.title_b,
            model_version="error", source="fallback",
        )


@router.post("/plagiarism-trends/compare-pdf", response_model=CompareResponse)
async def compare_two_pdfs(
    file_a: UploadFile = File(..., description="First PDF"),
    file_b: UploadFile = File(..., description="Second PDF"),
    title_a: Optional[str] = Form(None),
    title_b: Optional[str] = Form(None),
    top_pairs: int = Form(5),
) -> CompareResponse:
    """Upload two PDFs and run the same comparison pipeline used for raw text."""
    if not (file_a.filename and file_a.filename.lower().endswith(".pdf")
            and file_b.filename and file_b.filename.lower().endswith(".pdf")):
        raise HTTPException(status_code=400, detail="Both files must be .pdf")

    bytes_a = await file_a.read()
    bytes_b = await file_b.read()
    if not bytes_a or not bytes_b:
        raise HTTPException(status_code=400, detail="One or both files are empty")
    if max(len(bytes_a), len(bytes_b)) > 25 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Each PDF must be ≤ 25 MB")

    from app.services import pdf_extractor, plagiarism_analyzer
    ext_a = pdf_extractor.extract_text(bytes_a)
    ext_b = pdf_extractor.extract_text(bytes_b)

    text_a = ext_a.get("text", "")
    text_b = ext_b.get("text", "")
    if len(text_a) < 100 or len(text_b) < 100:
        warn = ext_a.get("warning") if len(text_a) < 100 else ext_b.get("warning")
        raise HTTPException(
            status_code=422,
            detail=warn or "Extracted text too short — both PDFs need ≥100 chars of selectable text.",
        )

    result = plagiarism_analyzer.compare_papers(text_a, text_b, top_pairs=top_pairs)
    if not result.get("loaded"):
        raise HTTPException(status_code=503, detail="Plagiarism analyzer not available")

    return CompareResponse(
        document_similarity=result["document_similarity"],
        ngram_jaccard=result["ngram_jaccard"],
        ngram_overlap_in_a=result["ngram_overlap_in_a"],
        ngram_overlap_in_b=result["ngram_overlap_in_b"],
        risk_score=result["risk_score"],
        risk_level=result["risk_level"],
        flagged_pairs=[FlaggedSentencePair(**p) for p in result.get("flagged_pairs", [])],
        n_sentences_a=result.get("n_sentences_a", 0),
        n_sentences_b=result.get("n_sentences_b", 0),
        title_a=title_a or file_a.filename or "Paper A",
        title_b=title_b or file_b.filename or "Paper B",
        model_version=result.get("model_version", "unknown"),
        source="local",
    )


class CompareReportRequest(BaseModel):
    result: dict[str, Any]
    title_a: str = "Paper A"
    title_b: str = "Paper B"


@router.post("/plagiarism-trends/compare/report", response_class=HTMLResponse)
async def compare_report(req: CompareReportRequest) -> HTMLResponse:
    """Render a comparison result as a downloadable HTML report."""
    from app.services import plagiarism_analyzer
    return HTMLResponse(content=plagiarism_analyzer.generate_compare_report_html(
        req.result, title_a=req.title_a, title_b=req.title_b,
    ))


@router.get("/plagiarism-trends/status")
async def plagiarism_status() -> dict:
    try:
        from app.services import plagiarism_analyzer
        return plagiarism_analyzer.get_model_info()
    except Exception as e:
        return {"loaded": False, "error": str(e)}
