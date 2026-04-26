"""RAG retrieval + Gemini-powered answer generation."""

from __future__ import annotations

import logging
import sys
import os
from typing import Any, Dict, List, Optional

from .supabase_client import get_supabase

logger = logging.getLogger(__name__)

_services_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, _services_root)


def retrieve(
    query_embedding: List[float],
    paper_ids: Optional[List[str]] = None,
    top_k: int = 8,
    threshold: float = 0.6,
) -> List[Dict[str, Any]]:
    sb = get_supabase()
    try:
        resp = sb.rpc(
            "search_paper_chunks",
            {
                "query_embedding": query_embedding,
                "target_paper_ids": paper_ids,
                "match_threshold": threshold,
                "match_count": top_k,
            },
        ).execute()
        return resp.data or []
    except Exception as e:
        logger.warning("search_paper_chunks RPC failed: %s", e)
        return []


def assemble_context(chunks: List[Dict[str, Any]], max_chars: int = 12000) -> str:
    blocks = []
    total = 0
    for c in chunks:
        title = c.get("paper_title") or "Untitled"
        section = c.get("section_heading") or ""
        text = c.get("chunk_text") or ""
        block = f"[{title} — {section}]\n{text}"
        if total + len(block) > max_chars:
            break
        blocks.append(block)
        total += len(block)
    return "\n\n---\n\n".join(blocks)


def build_answer(question: str, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Produce a grounded answer with citations using Gemini."""
    if not chunks:
        return {
            "answer": (
                "I couldn't find anything in the uploaded papers that answers that. "
                "Try rephrasing or upload additional papers on this topic."
            ),
            "citations": [],
            "retrieval_scores": {"avg_score": 0.0, "max_score": 0.0, "chunks_used": 0},
        }

    context = assemble_context(chunks)

    try:
        from shared.gemini_client import generate

        prompt = f"""You are an expert research assistant. Answer the question based ONLY on the provided paper excerpts.
Be precise, cite specific papers when relevant, and acknowledge if the papers don't fully address the question.

Paper excerpts:
{context}

Question: {question}

Provide a clear, well-structured answer:"""

        answer_text = generate(prompt, temperature=0.2, max_tokens=1024)

    except Exception as e:
        logger.warning("Gemini answer generation failed: %s — using templated fallback", e)
        bullets = []
        for c in chunks[:4]:
            snippet = (c.get("chunk_text") or "")[:300].strip()
            title = c.get("paper_title") or "Untitled"
            section = c.get("section_heading") or ""
            bullets.append(f"- According to *{title}* ({section}): {snippet}")
        answer_text = (
            f"Based on the {len(chunks)} most relevant passages from your papers:\n\n"
            + "\n".join(bullets)
        )

    citations = [
        {
            "paper_id": c.get("paper_id"),
            "paper_title": c.get("paper_title"),
            "section": c.get("section_heading"),
            "score": c.get("similarity"),
        }
        for c in chunks
    ]
    scores = [c.get("similarity") or 0.0 for c in chunks]
    return {
        "answer": answer_text,
        "citations": citations,
        "retrieval_scores": {
            "avg_score": sum(scores) / max(1, len(scores)),
            "max_score": max(scores) if scores else 0.0,
            "chunks_used": len(chunks),
        },
    }
