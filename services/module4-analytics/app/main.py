"""FastAPI entrypoint for Module 4 — Performance Analytics."""

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

from .routers import trends, quality, dashboard, mindmap, prediction, papers
from .services.model_loader import load_all_models, get_status

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Researchly — Module 4 (Analytics)",
    description="Trend forecasting, quality scoring, dashboards, concept mind maps, success prediction, paper upload",
    version="1.0.0",
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
    return {
        "status": "ok",
        "service": "module4-analytics",
        "version": "1.0.0",
        "models": get_status(),
    }


app.include_router(trends.router, prefix="/analytics", tags=["trends"])
app.include_router(quality.router, prefix="/analytics", tags=["quality"])
app.include_router(dashboard.router, prefix="/analytics", tags=["dashboard"])
app.include_router(mindmap.router, prefix="/analytics", tags=["mindmap"])
app.include_router(prediction.router, prefix="/analytics", tags=["prediction"])
app.include_router(papers.router, prefix="/analytics", tags=["papers"])


@app.on_event("startup")
async def startup() -> None:
    logger.info("Module 4 (Analytics) starting up — loading trained models...")
    results = load_all_models()
    loaded = sum(1 for v in results.values() if v)
    logger.info("Module 4 startup complete: %d/%d models loaded", loaded, len(results))
