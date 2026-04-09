"""Supervisor matching endpoint — SBERT cosine + multi-factor scoring."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()


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

    TODO (Phase 4): Embed student interests/abstract → call Supabase RPC
    match_supervisors() → compute multi-factor score (topic_sim, expertise_match,
    workload_factor, availability) → rank → explain.
    """
    return MatchSupervisorsResponse(matches=[])
