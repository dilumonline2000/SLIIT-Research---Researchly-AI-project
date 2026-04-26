"""
Production inference service for supervisor matching.
Uses the fine-tuned SBERT model loaded from models/trained_supervisor_matcher/
Falls back to base all-MiniLM-L6-v2 if fine-tuned model not available.
"""

import os
import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional
from sentence_transformers import SentenceTransformer

BASE_DIR = Path(__file__).parent.parent.parent
MODEL_DIR = BASE_DIR / "models" / "trained_supervisor_matcher"
FALLBACK = "sentence-transformers/all-MiniLM-L6-v2"

_model: Optional[SentenceTransformer] = None


def _cosine_similarity(a: list, b: list) -> float:
    """Compute cosine similarity between two embedding vectors."""
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))


def load_model() -> SentenceTransformer:
    """
    Load fine-tuned model. Falls back to base model if not trained yet.

    Returns:
        SentenceTransformer: Loaded embedding model (384-dim all-MiniLM-L6-v2 based)
    """
    global _model
    if _model:
        return _model

    model_path = MODEL_DIR if MODEL_DIR.exists() else FALLBACK

    _model = SentenceTransformer(str(model_path))
    version = "fine-tuned-v1" if MODEL_DIR.exists() else "base-pretrained"

    print(f"[SupervisorMatcher] Model loaded: {model_path} ({version})")
    return _model


async def match_supervisors(
    student_proposal: str,
    top_k: int = 5,
    min_similarity: float = 0.45,
) -> List[Dict]:
    """
    Match a student research proposal to the top-K supervisors.

    Args:
        student_proposal: Student's research proposal or topic description (free text)
        top_k: Number of supervisors to return (default 5)
        min_similarity: Minimum cosine similarity threshold (default 0.45)

    Returns:
        List of dicts with supervisor info + similarity score + explanation
        Schema:
        {
            "supervisor_id": int,
            "name": str,
            "email": str,
            "department": str,
            "research_cluster": str,
            "research_interests": List[str],
            "availability": bool,
            "current_students": int,
            "max_students": int,
            "similarity_score": float,
            "multi_factor_score": float,
            "explanation": str,
        }
    """
    model = load_model()

    # Encode student query using the model
    student_embedding = model.encode(student_proposal).tolist()

    # For now, we'll do local matching if embeddings aren't in Supabase yet
    # In production, this would query Supabase pgvector RPC function
    # But since we haven't uploaded yet, we'll try to load supervisors locally

    try:
        # Try to load pre-computed embeddings if they exist
        emb_file = BASE_DIR / "data" / "supervisors_with_embeddings.json"
        if emb_file.exists():
            with open(emb_file, encoding="utf-8") as f:
                supervisors = json.load(f)

            # Score all supervisors
            scored = []
            for sup in supervisors:
                if not sup.get("embedding"):
                    continue

                sim = _cosine_similarity(student_embedding, sup["embedding"])
                if sim < min_similarity:
                    continue

                # Availability factor
                avail_factor = 1.0
                if not sup.get("availability", True):
                    avail_factor = 0.0  # Unavailable
                elif sup.get("current_students", 0) >= sup.get("max_students", 5):
                    avail_factor = 0.3  # Full capacity

                # Multi-factor score: 70% similarity + 30% availability
                final_score = (sim * 0.70) + (avail_factor * 0.30)

                # Generate explanation
                explanation = _build_explanation(
                    student_proposal, sup, sim
                )

                scored.append(
                    {
                        "supervisor_id": sup["id"],
                        "name": sup["name"],
                        "email": sup["email"],
                        "department": sup["department"],
                        "research_cluster": sup["research_cluster"],
                        "research_interests": sup.get("research_interests", []),
                        "availability": sup.get("availability", True),
                        "current_students": sup.get("current_students", 0),
                        "max_students": sup.get("max_students", 5),
                        "similarity_score": round(sim, 4),
                        "multi_factor_score": round(final_score, 4),
                        "explanation": explanation,
                    }
                )

            # Sort by multi-factor score, return top_k
            scored.sort(key=lambda x: x["multi_factor_score"], reverse=True)
            return scored[:top_k]
        else:
            # Embeddings not computed yet
            return []

    except Exception as e:
        print(f"[SupervisorMatcher] Error matching supervisors: {e}")
        return []


def _build_explanation(query: str, sup: dict, sim: float) -> str:
    """Generate a human-readable explanation for why this supervisor matched."""
    interests = sup.get("research_interests", [])
    name = sup.get("name", "This supervisor")

    query_lower = query.lower()
    matched_interests = [
        i for i in interests if any(word in query_lower for word in i.lower().split())
    ]

    if matched_interests:
        return (
            f"{name} is a strong match ({sim * 100:.0f}% similarity) because their "
            f"research in {', '.join(matched_interests[:2])} aligns directly with "
            f"your proposed topic."
        )
    elif sim > 0.70:
        return (
            f"{name} is an excellent match ({sim * 100:.0f}% similarity) with "
            f"closely related expertise in {', '.join(interests[:2])}."
        )
    elif sim > 0.55:
        return (
            f"{name} could supervise your work ({sim * 100:.0f}% similarity). "
            f"Their background in {', '.join(interests[:2])} provides relevant context."
        )
    else:
        return (
            f"{name} has some relevant expertise ({sim * 100:.0f}% similarity) "
            f"in {', '.join(interests[:2])}."
        )
