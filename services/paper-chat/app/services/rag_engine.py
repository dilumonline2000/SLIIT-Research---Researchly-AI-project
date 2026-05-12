"""RAG retrieval + Gemini-powered answer generation."""

from __future__ import annotations

import logging
import re
import sys
import os
from typing import Any, Dict, List, Optional

from .supabase_client import get_supabase

logger = logging.getLogger(__name__)

_services_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, _services_root)


def _keyword_search(
    paper_ids: Optional[List[str]],
    query: str,
    top_k: int,
) -> List[Dict[str, Any]]:
    """Keyword-overlap fallback used when chunks have no vector embeddings."""
    sb = get_supabase()
    try:
        q = (
            sb.table("paper_chunks")
            .select("id,paper_id,chunk_text,chunk_type,section_heading,page_start,page_end")
            .limit(min(top_k * 25, 300))
        )
        if paper_ids:
            q = q.in_("paper_id", paper_ids)
        rows = q.execute().data or []
        if not rows:
            return []

        # Score by keyword overlap (words > 3 chars as simple stopword filter)
        q_words = set(w.lower() for w in re.findall(r"\w+", query) if len(w) > 3)

        def _score(row: Dict[str, Any]) -> float:
            text = (row.get("chunk_text") or "").lower()
            if not q_words:
                return 0.0
            return sum(1 for w in q_words if w in text) / len(q_words)

        scored = sorted(((row, _score(row)) for row in rows), key=lambda x: x[1], reverse=True)

        # Fetch paper titles for the matched paper IDs
        pid_set = list({r["paper_id"] for r, _ in scored[:top_k] if r.get("paper_id")})
        title_map: Dict[str, str] = {}
        if pid_set:
            try:
                papers = (
                    sb.table("uploaded_papers")
                    .select("id,title")
                    .in_("id", pid_set)
                    .execute()
                    .data or []
                )
                title_map = {p["id"]: p.get("title") or "Uploaded Paper" for p in papers}
            except Exception:
                pass

        result = []
        for row, sc in scored[:top_k]:
            if not row.get("chunk_text"):
                continue
            row["similarity"] = round(0.45 + sc * 0.40, 4)
            row["paper_title"] = title_map.get(row.get("paper_id", ""), "Uploaded Paper")
            result.append(row)
        return result

    except Exception as e:
        logger.warning("keyword_search fallback failed: %s", e)
        return []


def retrieve(
    query_embedding: List[float],
    paper_ids: Optional[List[str]] = None,
    top_k: int = 8,
    threshold: float = 0.6,
    query_text: str = "",
) -> List[Dict[str, Any]]:
    """Vector similarity search with keyword-based fallback for un-embedded chunks."""
    sb = get_supabase()
    chunks: List[Dict[str, Any]] = []

    if query_embedding:
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
            chunks = resp.data or []
        except Exception as e:
            logger.warning("search_paper_chunks RPC failed: %s", e)

    # Fallback: chunks exist but have no embeddings → keyword search
    if not chunks and query_text:
        logger.info("Vector search empty — using keyword fallback (paper_ids=%s)", paper_ids)
        chunks = _keyword_search(paper_ids, query_text, top_k)

    return chunks


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
