"""FastAPI entrypoint for Module 3 — Research Data Collection & Management."""

import logging
import os
import sys

# Bootstrap: put services/ on sys.path so routers can `from shared.x import y`
_services_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, _services_root)

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(_services_root, ".env"))
except ImportError:
    pass

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import pipeline, categorization, plagiarism_trends, summarizer, quality

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Researchly — Module 3 (Data Management)",
    description="Data pipelines, topic categorization, plagiarism trends, summarization",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "module3-data", "version": "0.1.0"}


app.include_router(pipeline.router, prefix="/data", tags=["pipeline"])
app.include_router(categorization.router, prefix="/data", tags=["categorization"])
app.include_router(plagiarism_trends.router, prefix="/data", tags=["trends"])
app.include_router(summarizer.router, prefix="/data", tags=["summarizer"])
app.include_router(quality.router, prefix="/data", tags=["quality"])


@app.on_event("startup")
async def startup() -> None:
    logger.info("Module 3 (Data Management) starting up")
