"""Supervisor matching endpoint — SBERT cosine + multi-factor scoring."""

from __future__ import annotations

import logging

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()
logger = logging.getLogger(__name__)


class MatchSupervisorsRequest(BaseModel):
    student_id: str
    research_interests: list[str] = Field(default_factory=list)
    abstract: str | None = None
    top_k: int = 5


class SupervisorMatch(BaseModel):
    supervisor_id: str
    similarity_score: float
    multi_factor_score: float
    match_factors: dict
    explanation: str


class MatchSupervisorsResponse(BaseModel):
    matches: list[SupervisorMatch]


@router.post("/supervisors", response_model=MatchSupervisorsResponse)
async def match_supervisors(req: MatchSupervisorsRequest) -> MatchSupervisorsResponse:
    """Find top-K supervisors for a student.

    1. Embed student interests/abstract via SBERT
    2. Call Supabase RPC match_supervisors() for vector similarity
    3. Compute multi-factor score (topic_sim, expertise_match, workload, availability)
    4. Rank and explain
    """
    try:
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "shared"))
        from services.shared.embedding_utils import embed
        from services.shared.supabase_client import get_supabase_admin
    except ImportError:
        try:
            from shared.embedding_utils import embed
            from shared.supabase_client import get_supabase_admin
        except ImportError:
            logger.warning("Shared utils not available")
            return MatchSupervisorsResponse(matches=[])

    # Build query text from interests + abstract
    query_parts = list(req.research_interests)
    if req.abstract:
        query_parts.append(req.abstract)
    query_text = ". ".join(query_parts) if query_parts else "general research"

    # Step 1: Embed
    query_vec = embed(query_text).tolist()

    # Step 2: Vector search
    try:
        sb = get_supabase_admin()
        result = sb.rpc(
            "match_supervisors",
            {"query_embedding": query_vec, "match_count": req.top_k * 2, "match_threshold": 0.3},
        ).execute()
        candidates = result.data or []
    except Exception as e:
        logger.warning("Supervisor matching failed: %s", e)
        candidates = []

    if not candidates:
        return MatchSupervisorsResponse(matches=[])

    # Step 3: Multi-factor scoring
    matches = []
    for cand in candidates:
        sim = float(cand.get("similarity", 0))

        # Workload factor: fewer current students = higher availability
        current_students = cand.get("current_student_count", 0) or 0
        max_students = cand.get("max_students", 10) or 10
        workload_factor = max(0, 1.0 - (current_students / max_students))

        # Expertise match: overlap between supervisor expertise areas and student interests
        supervisor_expertise = set((cand.get("expertise_areas") or []))
        student_interests_set = set(req.research_interests)
        if supervisor_expertise and student_interests_set:
            overlap = len(supervisor_expertise & student_interests_set)
            expertise_score = overlap / max(len(student_interests_set), 1)
        else:
            expertise_score = sim  # fallback to embedding similarity

        # Multi-factor weighted score
        multi_factor = (
            sim * 0.40 +
            expertise_score * 0.30 +
            workload_factor * 0.20 +
            0.10  # base availability
        )

        factors = {
            "topic_similarity": round(sim, 3),
            "expertise_match": round(expertise_score, 3),
            "workload_factor": round(workload_factor, 3),
            "availability": round(workload_factor, 3),
        }

        # Generate explanation
        parts = []
        if sim > 0.7:
            parts.append("Strong research alignment")
        elif sim > 0.5:
            parts.append("Good research overlap")
        else:
            parts.append("Moderate research connection")

        if workload_factor > 0.5:
            parts.append("currently has capacity for new students")
        else:
            parts.append("nearing full capacity")

        if expertise_score > 0.5:
            parts.append("strong expertise match")

        explanation = "; ".join(parts) + "."

        matches.append(SupervisorMatch(
            supervisor_id=str(cand.get("id", "")),
            similarity_score=round(sim, 4),
            multi_factor_score=round(multi_factor, 4),
            match_factors=factors,
            explanation=explanation,
        ))

    # Sort by multi-factor score
    matches.sort(key=lambda m: m.multi_factor_score, reverse=True)

    return MatchSupervisorsResponse(matches=matches[:req.top_k])
