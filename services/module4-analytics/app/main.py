"""FastAPI entrypoint for Module 4 — Performance Analytics."""

import logging
import os
import sys

# Bootstrap: put services/ on sys.path so routers can `from shared.x import y`
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import trends, quality, dashboard, mindmap, prediction

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Researchly — Module 4 (Analytics)",
    description="Trend forecasting, quality scoring, dashboards, concept mind maps, success prediction",
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
    return {"status": "ok", "service": "module4-analytics", "version": "0.1.0"}


app.include_router(trends.router, prefix="/analytics", tags=["trends"])
app.include_router(quality.router, prefix="/analytics", tags=["quality"])
app.include_router(dashboard.router, prefix="/analytics", tags=["dashboard"])
app.include_router(mindmap.router, prefix="/analytics", tags=["mindmap"])
app.include_router(prediction.router, prefix="/analytics", tags=["prediction"])


@app.on_event("startup")
async def startup() -> None:
    logger.info("Module 4 (Analytics) starting up")
