"""Data pipeline orchestration — kick off scrapers + ingestion."""

from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel, Field

router = APIRouter()


class ScrapeRequest(BaseModel):
    source: str = Field(..., pattern="^(ieee|arxiv|acm|sliit|scholar|semantic_scholar)$")
    query: str | None = None
    max_papers: int = 100


class ScrapeResponse(BaseModel):
    job_id: str
    source: str
    status: str


@router.post("/scrape", response_model=ScrapeResponse)
async def start_scrape(req: ScrapeRequest, background_tasks: BackgroundTasks) -> ScrapeResponse:
    """Kick off a scrape job in the background.

    TODO (Phase 2): Resolve scraper class from req.source, enqueue background
    task, create pipeline_runs row, return job_id for polling.
    """
    job_id = f"stub-{req.source}"
    return ScrapeResponse(job_id=job_id, source=req.source, status="queued")
