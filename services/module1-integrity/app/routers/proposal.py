"""Proposal generation endpoint.

Primary path: locally-trained proposal retriever (composes from top-K SLIIT papers).
Fallback path: Gemini prompt — only used when no local index is available.
"""

from __future__ import annotations

import logging
import os
import sys

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()
logger = logging.getLogger(__name__)

_services_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, _services_root)


class GenerateProposalRequest(BaseModel):
    topic: str = Field(..., min_length=1)
    domain: str | None = None
    user_id: str | None = None
    top_k: int = 5


class RetrievedPaper(BaseModel):
    paper_id: str = ""
    title: str = ""
    authors: list[str] = []
    year: int | str | None = None
    url: str = ""
    similarity: float = 0.0


class GeneratedProposal(BaseModel):
    problem_statement: str
    objectives: list[str]
    methodology: str
    expected_outcomes: str
    retrieved_papers: list[RetrievedPaper] = []
    retrieved_paper_ids: list[str] = []
    model_version: str = "unknown"
    base_model: str = "unknown"
    source: str = "unknown"  # "local" | "gemini" | "fallback"


@router.post("/generate", response_model=GeneratedProposal)
async def generate_proposal(req: GenerateProposalRequest) -> GeneratedProposal:
    """Generate a structured research proposal grounded in SLIIT papers.

    Strategy:
      1. Local retriever finds top-K similar SLIIT papers and composes a proposal.
      2. If unavailable, fall back to Gemini.
    """
    # ── 1. Local retriever ───────────────────────────────────────────────────
    try:
        from app.services import proposal_retriever

        result = proposal_retriever.generate(req.topic, domain=req.domain, top_k=req.top_k)
        if result.get("loaded"):
            return GeneratedProposal(
                problem_statement=result["problem_statement"],
                objectives=result["objectives"],
                methodology=result["methodology"],
                expected_outcomes=result["expected_outcomes"],
                retrieved_papers=[RetrievedPaper(**p) for p in result.get("retrieved_papers", [])],
                retrieved_paper_ids=[p["paper_id"] for p in result.get("retrieved_papers", []) if p.get("paper_id")],
                model_version=result.get("model_version", "unknown"),
                base_model=result.get("base_model", "unknown"),
                source="local",
            )
    except Exception as e:
        logger.warning("Local proposal retriever failed: %s — falling back to Gemini", e)

    # ── 2. Gemini fallback ───────────────────────────────────────────────────
    try:
        from shared.gemini_client import generate_json

        domain_context = f" in the domain of {req.domain}" if req.domain else ""

        prompt = f"""You are an expert academic research advisor. Generate a comprehensive research proposal for the following topic.

Research Topic: {req.topic}{domain_context}

Create a structured research proposal with:
- A clear problem statement identifying the research gap
- 3-5 specific, measurable research objectives
- A detailed methodology section describing the research approach
- Expected outcomes and contributions

Return as JSON:
{{
  "problem_statement": "Clear 2-3 sentence problem statement",
  "objectives": ["Objective 1: ...", "Objective 2: ...", "Objective 3: ..."],
  "methodology": "Detailed paragraph describing research methodology, data collection, analysis methods",
  "expected_outcomes": "Paragraph describing expected contributions and impact"
}}"""

        data = generate_json(prompt)
        return GeneratedProposal(
            problem_statement=data.get("problem_statement", ""),
            objectives=data.get("objectives", []),
            methodology=data.get("methodology", ""),
            expected_outcomes=data.get("expected_outcomes", ""),
            source="gemini",
        )
    except Exception as e:
        logger.error("Gemini proposal generation also failed: %s", e)

    return GeneratedProposal(
        problem_statement=f"Investigation of {req.topic} to address current limitations in the field.",
        objectives=[
            f"Conduct a comprehensive literature review on {req.topic}",
            "Identify key research gaps and opportunities",
            "Develop and evaluate a novel approach",
        ],
        methodology=f"Mixed-methods research combining systematic literature review with experimental evaluation in {req.topic}.",
        expected_outcomes=f"Novel contributions to {req.topic} with empirical validation.",
        source="fallback",
    )


@router.get("/status")
async def proposal_retriever_status() -> dict:
    """Health check for the local proposal retriever."""
    try:
        from app.services import proposal_retriever
        return proposal_retriever.get_model_info()
    except Exception as e:
        return {"loaded": False, "error": str(e)}
