"""Paper upload + processing endpoints.

The frontend uploads PDFs directly to Supabase Storage and creates the
uploaded_papers row. This service handles:
  - POST /papers/process            — run the full extraction pipeline
  - GET  /papers                    — list (proxied via gateway)
  - GET  /papers/{id}               — single paper
  - GET  /papers/{id}/training-data — JSON training payload
  - DELETE /papers/{id}
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

import httpx
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query

from ..schemas import PaperOut, ProcessRequest, TrainingDataOut
from ..services.chunk_manager import chunk_document
from ..services.pdf_processor import build_extracted_data
from ..services.supabase_client import get_supabase
from ..services.training_pipeline import queue_uploaded_paper

logger = logging.getLogger(__name__)
router = APIRouter()

_STORAGE_BUCKET = "research-papers"


def _extract_storage_path(file_url: str) -> Optional[str]:
    """Extract the storage object path from a Supabase storage public URL.

    Supabase public URLs look like:
      https://<project>.supabase.co/storage/v1/object/public/<bucket>/<path>
    Returns just <path> (everything after the bucket name), or None if the URL
    doesn't match the expected format.
    """
    try:
        marker = f"/object/public/{_STORAGE_BUCKET}/"
        idx = file_url.find(marker)
        if idx != -1:
            return file_url[idx + len(marker):]
        # Also handle /object/authenticated/
        marker2 = f"/object/authenticated/{_STORAGE_BUCKET}/"
        idx2 = file_url.find(marker2)
        if idx2 != -1:
            return file_url[idx2 + len(marker2):]
    except Exception:
        pass
    return None



def _update_status(sb, paper_id: str, status: str, error: Optional[str] = None, **extras: Any) -> None:
    payload: Dict[str, Any] = {"processing_status": status, "updated_at": datetime.now(timezone.utc).isoformat()}
    if error:
        payload["processing_error"] = error
    payload.update(extras)
    try:
        sb.table("uploaded_papers").update(payload).eq("id", paper_id).execute()
    except Exception as e:
        logger.warning("status update failed: %s", e)


def _process_paper_sync(paper_id: str) -> None:
    """Run the extraction pipeline for one paper. Designed to be called as a background task."""
    sb = get_supabase()
    try:
        # Fetch row
        row = (
            sb.table("uploaded_papers")
            .select("*")
            .eq("id", paper_id)
            .single()
            .execute()
            .data
        )
        if not row:
            logger.warning("paper %s not found", paper_id)
            return

        file_url = row.get("file_url")
        if not file_url:
            _update_status(sb, paper_id, "failed", "missing file_url")
            return

        _update_status(
            sb,
            paper_id,
            "extracting",
            processing_started_at=datetime.now(timezone.utc).isoformat(),
        )

        # Download PDF — try Supabase storage API first (works for public & private buckets),
        # fall back to direct HTTP for externally hosted files.
        pdf_bytes: bytes = b""
        storage_path = _extract_storage_path(file_url)
        if storage_path:
            try:
                pdf_bytes = sb.storage.from_("research-papers").download(storage_path)
                logger.info("Downloaded %s from Supabase storage (%d bytes)", storage_path, len(pdf_bytes))
            except Exception as dl_err:
                logger.warning("Supabase storage download failed (%s), trying direct HTTP: %s", storage_path, dl_err)
                pdf_bytes = b""

        if not pdf_bytes:
            with httpx.Client(timeout=60.0) as client:
                resp = client.get(file_url)
                resp.raise_for_status()
                pdf_bytes = resp.content
                logger.info("Downloaded %s via HTTP (%d bytes)", file_url, len(pdf_bytes))

        # Step 1-3: extract structured data
        extracted = build_extracted_data(pdf_bytes)
        metadata = extracted.get("metadata") or {}
        stats = extracted.get("statistics") or {}

        _update_status(sb, paper_id, "chunking")
        chunks = chunk_document(extracted)

        _update_status(sb, paper_id, "indexing")

        # Embed chunks using Gemini text-embedding-004 (768d) — matches the
        # paper_chunks.embedding column exactly, so no dimension mismatch.
        chunk_embeddings: dict[int, list] = {}
        try:
            from shared.gemini_client import embed as gemini_embed  # type: ignore

            for i, c in enumerate(chunks):
                text = c.get("chunk_text", "")
                if not text:
                    continue
                try:
                    chunk_embeddings[i] = gemini_embed(text)
                except Exception as chunk_err:
                    logger.warning("Gemini embed failed for chunk %d: %s", i, chunk_err)
        except Exception as emb_err:
            logger.warning("Embedding step skipped entirely: %s", emb_err)

        chunk_rows = []
        for idx, c in enumerate(chunks):
            row: dict = {
                "paper_id": paper_id,
                "chunk_index": c["chunk_index"],
                "chunk_text": c["chunk_text"],
                "chunk_type": c.get("chunk_type", "other"),
                "section_heading": c.get("section_heading"),
                "page_start": c.get("page_start"),
                "page_end": c.get("page_end"),
                "token_count": c.get("token_count"),
            }
            if idx in chunk_embeddings:
                row["embedding"] = chunk_embeddings[idx]
            chunk_rows.append(row)

        # Idempotency: clear any existing chunks for this paper
        try:
            sb.table("paper_chunks").delete().eq("paper_id", paper_id).execute()
        except Exception:
            pass

        # Batch insert chunks
        BATCH = 50
        for i in range(0, len(chunk_rows), BATCH):
            sb.table("paper_chunks").insert(chunk_rows[i : i + BATCH]).execute()

        # Update paper row with final metadata + status
        update_payload: Dict[str, Any] = {
            "title": metadata.get("title"),
            "authors": metadata.get("authors") or [],
            "abstract": metadata.get("abstract"),
            "keywords": metadata.get("keywords") or [],
            "publication_year": metadata.get("year"),
            "venue": metadata.get("venue"),
            "doi": metadata.get("doi"),
            "page_count": stats.get("page_count"),
            "references_list": extracted.get("references"),
            "extracted_data": extracted,
            "processing_status": "ready",
            "processing_completed_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "used_by_modules": ["module1", "module2", "module3", "module4"],
        }
        # Do NOT include embedding in update — see NOTE above about dimension mismatch.
        sb.table("uploaded_papers").update(update_payload).eq("id", paper_id).execute()
        logger.info("paper %s: title=%r, %d chunks stored (no vectors)", paper_id, metadata.get("title"), len(chunk_rows))

        # Queue training data
        queue_uploaded_paper(paper_id, extracted)

        logger.info("paper %s processed: %d chunks", paper_id, len(chunk_rows))

    except Exception as e:
        logger.exception("processing failed for %s", paper_id)
        try:
            _update_status(get_supabase(), paper_id, "failed", str(e)[:500])
        except Exception:
            pass


@router.post("/process")
async def process_paper(req: ProcessRequest, background: BackgroundTasks) -> Dict[str, Any]:
    background.add_task(_process_paper_sync, str(req.paper_id))
    return {"paper_id": str(req.paper_id), "status": "queued"}


@router.post("/{paper_id}/reprocess")
async def reprocess_paper(paper_id: UUID, background: BackgroundTasks) -> Dict[str, Any]:
    background.add_task(_process_paper_sync, str(paper_id))
    return {"paper_id": str(paper_id), "status": "queued"}


@router.get("")
async def list_papers(
    user_id: Optional[str] = Query(default=None),
    limit: int = Query(default=50, le=200),
) -> Dict[str, Any]:
    sb = get_supabase()
    q = sb.table("uploaded_papers").select(
        "id,title,authors,abstract,page_count,processing_status,processing_error,created_at,publication_year,keywords"
    )
    if user_id:
        q = q.eq("user_id", user_id)
    try:
        rows = q.order("created_at", desc=True).limit(limit).execute().data or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"papers": rows, "count": len(rows)}


@router.get("/{paper_id}")
async def get_paper(paper_id: UUID) -> Dict[str, Any]:
    sb = get_supabase()
    try:
        row = sb.table("uploaded_papers").select("*").eq("id", str(paper_id)).single().execute().data
    except Exception:
        row = None
    if not row:
        raise HTTPException(status_code=404, detail="paper not found")
    return row


@router.get("/{paper_id}/chunks")
async def get_chunks(paper_id: UUID, limit: int = Query(default=200, le=500)) -> Dict[str, Any]:
    sb = get_supabase()
    rows = (
        sb.table("paper_chunks")
        .select("id,chunk_index,chunk_text,chunk_type,section_heading,page_start,page_end,token_count")
        .eq("paper_id", str(paper_id))
        .order("chunk_index")
        .limit(limit)
        .execute()
        .data
        or []
    )
    return {"chunks": rows, "count": len(rows)}


@router.get("/{paper_id}/training-data", response_model=TrainingDataOut)
async def get_training_data(paper_id: UUID) -> TrainingDataOut:
    sb = get_supabase()
    row = sb.table("uploaded_papers").select("extracted_data,created_at").eq("id", str(paper_id)).single().execute().data
    if not row:
        raise HTTPException(status_code=404, detail="paper not found")
    extracted = row.get("extracted_data") or {}
    metadata = extracted.get("metadata") or {}
    data = {
        "for_sbert_training": {
            "anchor_text": metadata.get("abstract") or "",
            "metadata": {"title": metadata.get("title"), "year": metadata.get("year")},
        },
        "for_scibert_classification": {
            "text": (metadata.get("abstract") or "") + "\n" + (metadata.get("title") or ""),
            "labels": metadata.get("keywords") or [],
        },
        "for_summarization": {
            "abstract_as_summary": metadata.get("abstract") or "",
            "full_text": (extracted.get("full_text") or "")[:20000],
        },
        "for_quality_scoring": extracted.get("statistics") or {},
        "for_rag_retrieval": {"sections": len(extracted.get("sections") or [])},
    }
    return TrainingDataOut(
        paper_id=paper_id,
        version="1.0",
        extracted_at=datetime.now(timezone.utc),
        data=data,
    )


@router.delete("/{paper_id}")
async def delete_paper(paper_id: UUID) -> Dict[str, Any]:
    sb = get_supabase()
    try:
        sb.table("uploaded_papers").delete().eq("id", str(paper_id)).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"deleted": str(paper_id)}
