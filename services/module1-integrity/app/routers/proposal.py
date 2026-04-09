"""Proposal generator — RAG over pgvector + LoRA-tuned LLM."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()


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
    """Generate a structured proposal outline.

    TODO (Phase 3/4): Embed topic → pgvector match_papers() → build context →
    call LoRA-tuned Mistral-7B / Llama-2-7b → parse JSON output.
    """
    return GeneratedProposal(
        problem_statement=f"(stub) problem statement for: {req.topic}",
        objectives=[],
        methodology="",
        expected_outcomes="",
    )
