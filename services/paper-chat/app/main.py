"""FastAPI entrypoint for the Paper Upload + RAG Chat + Continuous Training service.

This is a NEW cross-cutting service (port 8005) that is additive — it does not
modify any of the existing module1-4 services. The API gateway proxies to it
under /api/v1/papers, /api/v1/chat, /api/v1/language and /api/v1/training.
"""

import logging
import os
import sys

# Bootstrap: put services/ on sys.path so `from shared.x import y` works
_services_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, _services_root)

# Load .env from services/ directory (shared by all Python services)
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(_services_root, ".env"))
except ImportError:
    pass

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import upload, chat, training, language, local_inference
from .services.model_loader import load_all_trained_models

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Researchly — Paper Chat & Continuous Training",
    description="PDF upload pipeline, multilingual RAG chatbot, continuous learning queue",
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
    return {"status": "ok", "service": "paper-chat", "version": "0.1.0"}


app.include_router(upload.router, prefix="/papers", tags=["papers"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(language.router, prefix="/language", tags=["language"])
app.include_router(training.router, prefix="/training", tags=["training"])
app.include_router(local_inference.router, prefix="/local", tags=["local-inference"])


@app.on_event("startup")
async def startup() -> None:
    logger.info("paper-chat service starting up")
    # Load any trained local models (Citation NER, SBERT, etc.)
    load_all_trained_models()
