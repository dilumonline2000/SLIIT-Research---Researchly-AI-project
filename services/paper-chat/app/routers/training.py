"""Training pipeline endpoints — status, queue listing, manual trigger, model registry."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Query

from ..schemas import TrainingStatus
from ..services.supabase_client import get_supabase
from ..services.training_pipeline import get_status

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/status", response_model=TrainingStatus)
async def status() -> TrainingStatus:
    s = get_status()
    return TrainingStatus(**s)


@router.get("/queue")
async def list_queue(
    limit: int = Query(default=50, le=200),
    target_model: str | None = Query(default=None),
) -> Dict[str, Any]:
    sb = get_supabase()
    q = sb.table("training_data_queue").select(
        "id,source_type,target_models,status,quality_score,created_at"
    ).order("created_at", desc=True).limit(limit)
    if target_model:
        q = q.contains("target_models", [target_model])
    rows = q.execute().data or []
    return {"items": rows, "count": len(rows)}


@router.post("/trigger")
async def trigger_training(target_model: str | None = None) -> Dict[str, Any]:
    """Mark pending items as queued for the next batch.

    Real training is run by ml/training/continuous_trainer.py — this endpoint
    just signals the next batch is ready and returns the count.
    """
    sb = get_supabase()
    q = sb.table("training_data_queue").update({"status": "queued"}).eq("status", "pending")
    if target_model:
        q = q.contains("target_models", [target_model])
    try:
        res = q.execute()
        count = len(res.data or [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"queued": count, "target_model": target_model}


@router.get("/models")
async def list_models() -> Dict[str, Any]:
    sb = get_supabase()
    try:
        rows = (
            sb.table("model_versions")
            .select("*")
            .order("created_at", desc=True)
            .limit(100)
            .execute()
            .data
            or []
        )
    except Exception as e:
        logger.warning("model_versions query failed: %s", e)
        rows = []
    return {"models": rows, "count": len(rows)}
