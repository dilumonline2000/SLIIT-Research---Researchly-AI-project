"""FastAPI entrypoint for Module 1 — Research Integrity & Compliance."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import citation, gap_analysis, proposal, plagiarism, mindmap

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Researchly — Module 1 (Integrity)",
    description="Citation parsing, gap analysis, proposal generation, plagiarism detection, mind maps",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # API Gateway is the only intended caller
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "module1-integrity", "version": "0.1.0"}


# Routers
app.include_router(citation.router, prefix="/citations", tags=["citations"])
app.include_router(gap_analysis.router, prefix="/gaps", tags=["gaps"])
app.include_router(proposal.router, prefix="/proposals", tags=["proposals"])
app.include_router(plagiarism.router, prefix="/plagiarism", tags=["plagiarism"])
app.include_router(mindmap.router, prefix="/mindmaps", tags=["mindmaps"])


@app.on_event("startup")
async def startup() -> None:
    logger.info("Module 1 (Integrity) starting up")
