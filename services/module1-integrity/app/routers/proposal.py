"""Proposal generator — powered by Gemini."""

from __future__ import annotations

import logging
import sys
import os

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()
logger = logging.getLogger(__name__)

_services_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, _services_root)


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
    """Generate a structured research proposal using Gemini."""
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
  "objectives": [
    "Objective 1: ...",
    "Objective 2: ...",
    "Objective 3: ..."
  ],
  "methodology": "Detailed paragraph describing research methodology, data collection, analysis methods",
  "expected_outcomes": "Paragraph describing expected contributions and impact"
}}"""

    try:
        data = generate_json(prompt)
        return GeneratedProposal(
            problem_statement=data.get("problem_statement", ""),
            objectives=data.get("objectives", []),
            methodology=data.get("methodology", ""),
            expected_outcomes=data.get("expected_outcomes", ""),
            retrieved_paper_ids=[],
        )
    except Exception as e:
        logger.error("Gemini proposal generation failed: %s", e)
        return GeneratedProposal(
            problem_statement=f"Investigation of {req.topic} to address current limitations in the field.",
            objectives=[
                f"Conduct a comprehensive literature review on {req.topic}",
                "Identify key research gaps and opportunities",
                "Develop and evaluate a novel approach",
            ],
            methodology=f"Mixed-methods research combining systematic literature review with experimental evaluation in {req.topic}.",
            expected_outcomes=f"Novel contributions to {req.topic} with empirical validation.",
            retrieved_paper_ids=[],
        )
