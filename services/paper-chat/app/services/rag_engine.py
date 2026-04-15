"""RAG retrieval + grounded answer assembly.

Generation is intentionally LLM-free by default: the assembled answer
synthesises retrieved chunks with explicit citations. If an LLM
backend (transformers GPT2 or OpenAI-compatible) is available it can
upgrade the answer, but the fallback always works.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from .supabase_client import get_supabase

logger = logging.getLogger(__name__)


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
    """Produce a grounded answer with citations.

    Uses a templated synthesis when no LLM is configured. This is sufficient
    to demo the RAG flow end-to-end and is upgradable later.
    """
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

    # Optional LLM upgrade
    answer_text: Optional[str] = None
    try:
        from transformers import pipeline  # type: ignore

        pipe = pipeline("text-generation", model="distilgpt2", max_new_tokens=160)
        prompt = (
            "You are a research paper assistant. Use the context below to answer.\n"
            f"Context:\n{context[:2000]}\n\nQuestion: {question}\nAnswer:"
        )
        out = pipe(prompt, do_sample=False)[0]["generated_text"]
        answer_text = out.split("Answer:", 1)[-1].strip()
    except Exception:
        answer_text = None

    if not answer_text:
        # Templated synthesis from top chunks
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
