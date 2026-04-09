"""Peer recommendation — hybrid Collaborative Filtering + Content-Based."""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


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
    """Recommend peer collaborators using hybrid CF+CBF.

    TODO (Phase 4): Content-based via SBERT over student interests/proposals,
    collaborative via LightFM interaction matrix, hybrid via weighted blend.
    """
    return MatchPeersResponse(matches=[])
