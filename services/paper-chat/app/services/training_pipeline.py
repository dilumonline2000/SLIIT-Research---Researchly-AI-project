"""Continuous training queue helpers — append-only writes into training_data_queue."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from .supabase_client import get_supabase

logger = logging.getLogger(__name__)


def queue_uploaded_paper(paper_id: str, extracted: Dict[str, Any]) -> None:
    """Queue a freshly uploaded paper as training data for multiple models."""
    sb = get_supabase()
    metadata = extracted.get("metadata", {})
    payload = {
        "source_type": "uploaded_paper",
        "source_id": paper_id,
        "training_data": {
            "for_sbert_training": {
                "anchor_text": metadata.get("abstract") or "",
                "metadata": {
                    "title": metadata.get("title"),
                    "year": metadata.get("year"),
                },
            },
            "for_scibert_classification": {
                "text": (metadata.get("abstract") or "") + "\n" + (metadata.get("title") or ""),
                "labels": metadata.get("keywords") or [],
            },
            "for_summarization": {
                "full_text": extracted.get("full_text", "")[:20000],
                "abstract_as_summary": metadata.get("abstract") or "",
            },
            "for_quality_scoring": {
                "has_abstract": bool(metadata.get("abstract")),
                "reference_count": (extracted.get("statistics") or {}).get("reference_count", 0),
                "word_count": (extracted.get("statistics") or {}).get("word_count", 0),
            },
            "for_rag_retrieval": {
                "chunk_count": len(extracted.get("sections") or []),
            },
        },
        "target_models": [
            "sbert",
            "scibert_classifier",
            "summarizer",
            "quality_scorer",
            "rag_retriever",
        ],
        "status": "pending",
        "quality_score": 0.7,
    }
    try:
        sb.table("training_data_queue").insert(payload).execute()
    except Exception as e:
        logger.warning("queue_uploaded_paper failed: %s", e)


def queue_chat_qa(
    session_id: str,
    question: str,
    answer: str,
    language: str,
    paper_ids: List[str],
    rating: Optional[int] = None,
    is_helpful: Optional[bool] = None,
) -> None:
    sb = get_supabase()
    quality = 0.6
    if is_helpful is True:
        quality = 0.85
    if is_helpful is False:
        quality = 0.2
    payload = {
        "source_type": "chat_qa",
        "source_id": session_id,
        "training_data": {
            "question": question,
            "answer": answer,
            "language": language,
            "paper_ids": paper_ids,
            "user_rating": rating,
            "is_helpful": is_helpful,
        },
        "target_models": ["rag_retriever", "sbert"],
        "status": "pending",
        "quality_score": quality,
    }
    try:
        sb.table("training_data_queue").insert(payload).execute()
    except Exception as e:
        logger.warning("queue_chat_qa failed: %s", e)


def queue_feedback(message_id: str, rating: int, is_helpful: bool, feedback_text: Optional[str]) -> None:
    sb = get_supabase()
    payload = {
        "source_type": "user_feedback",
        "source_id": message_id,
        "training_data": {
            "message_id": message_id,
            "rating": rating,
            "feedback_text": feedback_text,
            "is_helpful": is_helpful,
        },
        "target_models": ["rag_retriever", "sbert", "proposal_llm"],
        "status": "pending",
        "quality_score": 0.9 if is_helpful else 0.3,
    }
    try:
        sb.table("training_data_queue").insert(payload).execute()
    except Exception as e:
        logger.warning("queue_feedback failed: %s", e)


def get_status() -> Dict[str, Any]:
    sb = get_supabase()
    out = {"pending": 0, "queued": 0, "completed": 0, "failed": 0, "by_model": {}}
    try:
        rows = sb.table("training_data_queue").select("status,target_models").execute().data or []
        for r in rows:
            s = r.get("status") or "pending"
            if s in out:
                out[s] += 1
            for m in r.get("target_models") or []:
                out["by_model"][m] = out["by_model"].get(m, 0) + 1
    except Exception as e:
        logger.warning("training status query failed: %s", e)
    return out
