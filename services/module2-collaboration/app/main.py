"""FastAPI entrypoint for Module 2 — Collaboration & Recommendation."""

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

from .routers import supervisor, peer, feedback, effectiveness

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Researchly — Module 2 (Collaboration)",
    description="Supervisor matching, peer recommendation, feedback sentiment, effectiveness scoring",
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
    return {"status": "ok", "service": "module2-collaboration", "version": "0.1.0"}


app.include_router(supervisor.router, prefix="/matching", tags=["matching"])
app.include_router(peer.router, prefix="/matching", tags=["matching"])
app.include_router(feedback.router, prefix="/feedback", tags=["feedback"])
app.include_router(effectiveness.router, prefix="/effectiveness", tags=["effectiveness"])


@app.on_event("startup")
async def startup() -> None:
    logger.info("Module 2 (Collaboration) starting up")
