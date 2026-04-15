"""Chat session + multilingual RAG message endpoints."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from ..schemas import (
    ChatMessageOut,
    CreateSessionRequest,
    FeedbackRequest,
    SendMessageRequest,
    SessionOut,
)
from ..services.language_service import normalise_query, translate
from ..services.rag_engine import build_answer, retrieve
from ..services.supabase_client import get_supabase
from ..services.training_pipeline import queue_chat_qa, queue_feedback

logger = logging.getLogger(__name__)
router = APIRouter()


def _embed(text: str) -> List[float]:
    from shared.embedding_utils import embed  # type: ignore

    return embed(text).tolist()


@router.post("/sessions", response_model=SessionOut)
async def create_session(req: CreateSessionRequest, user_id: Optional[str] = Query(default=None)) -> Dict[str, Any]:
    sb = get_supabase()
    payload = {
        "user_id": user_id,
        "title": req.title or "New chat",
        "session_type": req.session_type,
        "paper_ids": [str(p) for p in req.paper_ids],
        "preferred_language": req.preferred_language,
        "module_context": req.module_context,
    }
    try:
        row = sb.table("chat_sessions").insert(payload).execute().data
        return row[0] if isinstance(row, list) else row
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions")
async def list_sessions(user_id: Optional[str] = Query(default=None), limit: int = 50) -> Dict[str, Any]:
    sb = get_supabase()
    q = sb.table("chat_sessions").select("*").order("updated_at", desc=True).limit(limit)
    if user_id:
        q = q.eq("user_id", user_id)
    rows = q.execute().data or []
    return {"sessions": rows, "count": len(rows)}


@router.get("/sessions/{session_id}")
async def get_session(session_id: UUID) -> Dict[str, Any]:
    sb = get_supabase()
    session = sb.table("chat_sessions").select("*").eq("id", str(session_id)).single().execute().data
    if not session:
        raise HTTPException(status_code=404, detail="session not found")
    messages = (
        sb.table("chat_messages")
        .select("*")
        .eq("session_id", str(session_id))
        .order("created_at")
        .execute()
        .data
        or []
    )
    return {"session": session, "messages": messages}


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: UUID) -> Dict[str, Any]:
    sb = get_supabase()
    sb.table("chat_sessions").delete().eq("id", str(session_id)).execute()
    return {"deleted": str(session_id)}


@router.patch("/sessions/{session_id}/papers")
async def update_session_papers(session_id: UUID, body: Dict[str, Any]) -> Dict[str, Any]:
    sb = get_supabase()
    paper_ids = body.get("paper_ids") or []
    sb.table("chat_sessions").update({"paper_ids": [str(p) for p in paper_ids]}).eq(
        "id", str(session_id)
    ).execute()
    return {"session_id": str(session_id), "paper_ids": paper_ids}


@router.post("/sessions/{session_id}/message", response_model=ChatMessageOut)
async def send_message(session_id: UUID, req: SendMessageRequest) -> Dict[str, Any]:
    """Non-streaming RAG message endpoint.

    SSE streaming can be added later — this endpoint returns the full
    answer as JSON so the frontend works end-to-end immediately.
    """
    sb = get_supabase()
    session = sb.table("chat_sessions").select("*").eq("id", str(session_id)).single().execute().data
    if not session:
        raise HTTPException(status_code=404, detail="session not found")

    paper_ids = session.get("paper_ids") or []

    # 1. Language detection + normalisation
    english_query, detected_lang, _is_singlish = normalise_query(req.content)
    response_language = req.language_override or detected_lang

    # 2. Embed query
    try:
        query_vec = _embed(english_query)
    except Exception as e:
        logger.warning("embed failed, retrieval will be empty: %s", e)
        query_vec = []

    # 3. Retrieve
    chunks = retrieve(query_vec, paper_ids=paper_ids if paper_ids else None) if query_vec else []

    # 4. Generate
    result = build_answer(english_query, chunks)

    # 5. Optional response translation
    answer = result["answer"]
    if response_language in ("si", "ta") and answer:
        answer = translate(answer, source="en", target=response_language)

    # 6. Persist user + assistant messages
    try:
        sb.table("chat_messages").insert(
            {
                "session_id": str(session_id),
                "role": "user",
                "content": req.content,
                "detected_language": detected_lang,
                "original_content": req.content,
            }
        ).execute()
        msg_row = (
            sb.table("chat_messages")
            .insert(
                {
                    "session_id": str(session_id),
                    "role": "assistant",
                    "content": answer,
                    "detected_language": detected_lang,
                    "response_language": response_language,
                    "retrieved_chunks": result.get("citations"),
                    "retrieval_scores": result.get("retrieval_scores"),
                    "citations": result.get("citations"),
                }
            )
            .execute()
            .data
        )
        # Update session
        sb.table("chat_sessions").update(
            {
                "last_message_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        ).eq("id", str(session_id)).execute()
    except Exception as e:
        logger.warning("persist messages failed: %s", e)
        msg_row = []

    # 7. Queue for training
    try:
        queue_chat_qa(
            str(session_id),
            req.content,
            answer,
            detected_lang,
            [str(p) for p in paper_ids],
        )
    except Exception:
        pass

    return msg_row[0] if msg_row else {
        "id": "00000000-0000-0000-0000-000000000000",
        "role": "assistant",
        "content": answer,
        "detected_language": detected_lang,
        "citations": result.get("citations"),
    }


@router.post("/sessions/{session_id}/feedback")
async def feedback(session_id: UUID, req: FeedbackRequest) -> Dict[str, Any]:
    sb = get_supabase()
    update: Dict[str, Any] = {}
    if req.rating is not None:
        update["user_rating"] = req.rating
    if req.is_helpful is not None:
        update["is_helpful"] = req.is_helpful
    if req.feedback_text is not None:
        update["user_feedback"] = req.feedback_text
    if update:
        sb.table("chat_messages").update(update).eq("id", str(req.message_id)).execute()
    queue_feedback(str(req.message_id), req.rating or 0, bool(req.is_helpful), req.feedback_text)
    return {"message_id": str(req.message_id), "ok": True}
