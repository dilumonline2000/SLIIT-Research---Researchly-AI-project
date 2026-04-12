"""Proposal generator — RAG over pgvector + LoRA-tuned LLM."""

from __future__ import annotations

import logging

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ..models.proposal_generator import ProposalGeneratorModel

router = APIRouter()
logger = logging.getLogger(__name__)

_proposal_model: ProposalGeneratorModel | None = None


def _get_model() -> ProposalGeneratorModel:
    global _proposal_model
    if _proposal_model is None:
        _proposal_model = ProposalGeneratorModel()
    return _proposal_model


class GenerateProposalRequest(BaseModel):
    topic: str = Field(..., min_length=1)
    domain: str | None = None
    user_id: str


class GeneratedProposal(BaseModel):
    problem_statement: str
    objectives: list[str]
    methodology: str
    expected_outcomes: str
    retrieved_paper_ids: list[str] = []


@router.post("/generate", response_model=GeneratedProposal)
async def generate_proposal(req: GenerateProposalRequest) -> GeneratedProposal:
    """Generate a structured proposal outline using RAG + LLM.

    1. Embed topic → pgvector match_papers() to retrieve context
    2. Build context string from retrieved papers
    3. Feed context + topic to the proposal generator model
    4. Parse structured JSON output
    """
    retrieved_ids: list[str] = []
    context_parts: list[str] = []

    # Step 1+2: RAG retrieval
    try:
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "shared"))
        from services.shared.embedding_utils import embed
        from services.shared.supabase_client import get_supabase_admin

        query_vec = embed(req.topic).tolist()
        sb = get_supabase_admin()
        result = sb.rpc(
            "match_papers",
            {"query_embedding": query_vec, "match_count": 5, "match_threshold": 0.5},
        ).execute()

        for paper in (result.data or []):
            retrieved_ids.append(str(paper.get("id", "")))
            title = paper.get("title", "")
            abstract = paper.get("abstract", "")
            context_parts.append(f"- {title}: {abstract[:300]}")
    except Exception as e:
        logger.warning("RAG retrieval failed: %s — generating without context", e)

    context = "\n".join(context_parts) if context_parts else f"Research area: {req.topic}"
    if req.domain:
        context = f"Domain: {req.domain}\n{context}"

    # Step 3: Generate proposal
    gap = f"Research gap in {req.topic} that needs investigation"
    model = _get_model()

    try:
        raw = model.generate_proposal(context=context, gap=gap)
    except Exception as e:
        logger.error("Proposal generation failed: %s", e)
        raw = {
            "problem_statement": f"Investigation of {req.topic} to address current limitations in the field.",
            "objectives": [
                f"Conduct comprehensive literature review on {req.topic}",
                "Identify key research gaps and opportunities",
                "Develop and evaluate a novel approach",
            ],
            "methodology": f"Mixed-methods research combining systematic literature review with experimental evaluation in {req.topic}.",
            "expected_outcomes": f"Novel contributions to {req.topic} with empirical validation.",
        }

    return GeneratedProposal(
        problem_statement=raw.get("problem_statement", ""),
        objectives=raw.get("objectives", []),
        methodology=raw.get("methodology", ""),
        expected_outcomes=raw.get("expected_outcomes", ""),
        retrieved_paper_ids=retrieved_ids,
    )
