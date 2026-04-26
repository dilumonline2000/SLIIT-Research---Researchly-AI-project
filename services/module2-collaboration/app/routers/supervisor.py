"""Supervisor matching endpoint — fine-tuned SBERT + multi-factor scoring."""

from __future__ import annotations

import logging

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.supervisor_matcher import match_supervisors as find_supervisors

router = APIRouter()
logger = logging.getLogger(__name__)


class MatchSupervisorsRequest(BaseModel):
    """Request to find matching supervisors for a student proposal.

    Can accept either:
    - A free-text `proposal` string (new way — uses fine-tuned SBERT)
    - Legacy format: `research_interests[]` + `abstract` (converted to proposal string)
    """

    proposal: str | None = None  # Free-text research proposal (new)
    student_id: str | None = None  # Optional student ID for logging
    research_interests: list[str] = Field(default_factory=list)  # Legacy format
    abstract: str | None = None  # Legacy format
    top_k: int = 5
    min_similarity: float = 0.45


class SupervisorMatch(BaseModel):
    supervisor_id: int
    name: str
    email: str
    department: str
    research_cluster: str
    research_interests: list[str]
    similarity_score: float
    multi_factor_score: float
    explanation: str
    availability: bool
    current_students: int
    max_students: int


class MatchSupervisorsResponse(BaseModel):
    matches: list[SupervisorMatch]


@router.post("/supervisors", response_model=MatchSupervisorsResponse)
async def match_supervisors(req: MatchSupervisorsRequest) -> MatchSupervisorsResponse:
    """
    Find top-K supervisors for a student research proposal.

    Uses fine-tuned SBERT model trained on SLIIT supervisors + student proposals.

    Args:
        proposal: Free-text research proposal (recommended)
        research_interests: Legacy — array of interest keywords
        abstract: Legacy — research abstract
        top_k: Number of supervisors to return (default 5)
        min_similarity: Minimum similarity threshold (default 0.45)

    Returns:
        List of ranked supervisor matches with explanation
    """
    # Build query text
    if req.proposal:
        query_text = req.proposal
    else:
        # Legacy support: build from interests + abstract
        query_parts = list(req.research_interests)
        if req.abstract:
            query_parts.append(req.abstract)
        query_text = ". ".join(query_parts) if query_parts else "general research"

    if not query_text or not query_text.strip():
        logger.warning("Empty proposal provided")
        return MatchSupervisorsResponse(matches=[])

    try:
        # Call the supervisor matching service
        matches = await find_supervisors(
            student_proposal=query_text,
            top_k=req.top_k,
            min_similarity=req.min_similarity,
        )

        # Convert to response schema
        response_matches = [
            SupervisorMatch(
                supervisor_id=m["supervisor_id"],
                name=m["name"],
                email=m["email"],
                department=m["department"],
                research_cluster=m["research_cluster"],
                research_interests=m["research_interests"],
                similarity_score=m["similarity_score"],
                multi_factor_score=m["multi_factor_score"],
                explanation=m["explanation"],
                availability=m["availability"],
                current_students=m["current_students"],
                max_students=m["max_students"],
            )
            for m in matches
        ]

        logger.info(f"Found {len(response_matches)} supervisor matches for proposal")
        return MatchSupervisorsResponse(matches=response_matches)

    except Exception as e:
        logger.error(f"Supervisor matching failed: {e}", exc_info=True)
        return MatchSupervisorsResponse(matches=[])
