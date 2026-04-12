"""Peer recommendation — SBERT content-based similarity + Supabase pgvector."""

from __future__ import annotations

import logging

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger(__name__)


class MatchPeersRequest(BaseModel):
    student_id: str
    top_k: int = 10


class PeerMatch(BaseModel):
    peer_id: str
    similarity_score: float
    shared_interests: list[str] = []
    complementary_skills: list[str] = []
    recommendation_type: str  # content_based | collaborative | hybrid


class MatchPeersResponse(BaseModel):
    matches: list[PeerMatch]


@router.post("/peers", response_model=MatchPeersResponse)
async def match_peers(req: MatchPeersRequest) -> MatchPeersResponse:
    """Recommend peer collaborators using content-based matching.

    1. Fetch student profile (interests, proposal embedding) from Supabase
    2. Call match_peers() RPC for vector-based peer search
    3. Compute shared interests and complementary skills
    4. Rank by similarity
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
            return MatchPeersResponse(matches=[])

    sb = get_supabase_admin()

    # Step 1: Fetch student profile
    try:
        profile_result = sb.table("profiles").select("*").eq("id", req.student_id).single().execute()
        student = profile_result.data
    except Exception as e:
        logger.warning("Could not fetch student profile: %s", e)
        return MatchPeersResponse(matches=[])

    if not student:
        return MatchPeersResponse(matches=[])

    # Build query from student interests
    interests = student.get("research_interests") or []
    department = student.get("department") or ""
    query_text = ". ".join(interests) if interests else department

    if not query_text:
        return MatchPeersResponse(matches=[])

    query_vec = embed(query_text).tolist()

    # Step 2: Vector search for peers
    try:
        result = sb.rpc(
            "match_peers",
            {"query_embedding": query_vec, "match_count": req.top_k * 2, "match_threshold": 0.3},
        ).execute()
        candidates = result.data or []
    except Exception as e:
        logger.warning("Peer matching RPC failed: %s", e)
        candidates = []

    # Step 3: Score and enrich
    matches = []
    student_interests = set(i.lower() for i in interests)

    for cand in candidates:
        peer_id = str(cand.get("id", ""))
        if peer_id == req.student_id:
            continue

        sim = float(cand.get("similarity", 0))
        peer_interests = set(i.lower() for i in (cand.get("research_interests") or []))

        shared = list(student_interests & peer_interests)
        complementary = list(peer_interests - student_interests)

        matches.append(PeerMatch(
            peer_id=peer_id,
            similarity_score=round(sim, 4),
            shared_interests=shared[:5],
            complementary_skills=complementary[:5],
            recommendation_type="content_based",
        ))

    matches.sort(key=lambda m: m.similarity_score, reverse=True)

    return MatchPeersResponse(matches=matches[:req.top_k])
