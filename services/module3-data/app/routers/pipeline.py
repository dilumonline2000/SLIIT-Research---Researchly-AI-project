"""Data pipeline orchestration — kick off scrapers + ingestion."""

from __future__ import annotations

import logging
import uuid
from dataclasses import asdict
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

from ..scrapers.arxiv_scraper import ArxivScraper
from ..scrapers.semantic_scholar_scraper import SemanticScholarScraper
from ..scrapers.base_scraper import Paper

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory job tracker (replace with DB-backed in production)
_jobs: dict[str, dict] = {}

SourceType = Literal["ieee", "arxiv", "acm", "sliit", "scholar", "semantic_scholar"]


class ScrapeRequest(BaseModel):
    source: SourceType
    query: str | None = None
    max_papers: int = Field(default=100, ge=1, le=10000)


class ScrapeResponse(BaseModel):
    job_id: str
    source: str
    status: str


class JobStatus(BaseModel):
    job_id: str
    source: str
    status: str
    papers_collected: int
    error: str | None = None


def _get_scraper(source: SourceType) -> ArxivScraper | SemanticScholarScraper:
    """Resolve a scraper instance from the source name."""
    if source == "arxiv":
        return ArxivScraper(max_papers=10000)
    elif source == "semantic_scholar":
        return SemanticScholarScraper(max_papers=5000)
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Scraper for '{source}' is not yet implemented. "
            f"Available: arxiv, semantic_scholar.",
        )


async def _run_scrape_job(job_id: str, source: SourceType, query: str | None, max_papers: int) -> None:
    """Background task that runs the actual scraping."""
    _jobs[job_id]["status"] = "running"
    try:
        scraper = _get_scraper(source)

        if source == "arxiv":
            if query:
                papers = await scraper.scrape(query, max_papers)
            else:
                per_cat = max(max_papers // 11, 50)
                papers = await scraper.scrape_by_categories(max_per_category=per_cat)
        elif source == "semantic_scholar":
            if query:
                papers = await scraper.scrape(query, max_papers)
            else:
                per_topic = max(max_papers // 13, 50)
                papers = await scraper.scrape_by_topics(max_per_topic=per_topic)
        else:
            papers = []

        papers = papers[:max_papers]
        _jobs[job_id]["papers_collected"] = len(papers)
        _jobs[job_id]["status"] = "success"
        _jobs[job_id]["papers"] = [asdict(p) for p in papers]

        logger.info("Job %s complete: %d papers from %s", job_id, len(papers), source)

    except Exception as e:
        _jobs[job_id]["status"] = "failed"
        _jobs[job_id]["error"] = str(e)
        logger.error("Job %s failed: %s", job_id, e)


@router.post("/scrape", response_model=ScrapeResponse)
async def start_scrape(req: ScrapeRequest, background_tasks: BackgroundTasks) -> ScrapeResponse:
    """Kick off a scrape job in the background.

    Returns a job_id that can be polled with GET /data/scrape/{job_id}.
    """
    # Validate scraper exists before queuing
    _get_scraper(req.source)

    job_id = str(uuid.uuid4())[:8]
    _jobs[job_id] = {
        "source": req.source,
        "status": "queued",
        "papers_collected": 0,
        "error": None,
    }

    background_tasks.add_task(
        _run_scrape_job, job_id, req.source, req.query, req.max_papers
    )

    return ScrapeResponse(job_id=job_id, source=req.source, status="queued")


@router.get("/scrape/{job_id}", response_model=JobStatus)
async def get_scrape_status(job_id: str) -> JobStatus:
    """Check the status of a scrape job."""
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    return JobStatus(
        job_id=job_id,
        source=job["source"],
        status=job["status"],
        papers_collected=job["papers_collected"],
        error=job.get("error"),
    )
