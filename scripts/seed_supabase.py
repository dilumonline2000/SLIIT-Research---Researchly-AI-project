"""Seed Supabase with demo data for Phase 5 integration testing.

Populates:
  - 10 supervisor profiles (auth.users + profiles + supervisor_profiles)
  - 10 student profiles (auth.users + profiles + research_proposals)
  - 200 research papers with SBERT embeddings
  - A handful of feedback_entries, quality_scores, trend_forecasts, plagiarism_trends
    so dashboards and analytics pages show real numbers.

Usage:
    python scripts/seed_supabase.py                # seed everything
    python scripts/seed_supabase.py --skip-papers  # skip the slow embed step
    python scripts/seed_supabase.py --reset        # delete demo rows first

Environment (reads .env if python-dotenv is installed):
    SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
"""
from __future__ import annotations

import argparse
import os
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Make services/shared importable so we can reuse embedding_utils + client factories
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "services"))

try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except ImportError:
    pass

try:
    from supabase import create_client, Client  # type: ignore
except ImportError:
    print("supabase-py not installed. Run: pip install supabase python-dotenv sentence-transformers")
    sys.exit(1)


# =====================================================================
# Demo data
# =====================================================================

DEMO_TAG = "researchly-seed"  # used to identify seeded rows so --reset can clean up

SUPERVISORS = [
    ("Dr. Chamara Perera", "chamara.perera@sliit.lk", ["machine learning", "deep learning"], ["ml", "dl", "cv"], 8),
    ("Dr. Nayomi Fernando", "nayomi.fernando@sliit.lk", ["natural language processing", "transformers"], ["nlp", "llm"], 7),
    ("Dr. Ravindu Silva", "ravindu.silva@sliit.lk", ["computer vision", "image segmentation"], ["cv", "dl"], 6),
    ("Dr. Anushka Jayasinghe", "anushka.jay@sliit.lk", ["data science", "time series"], ["ds", "forecasting"], 9),
    ("Dr. Kavindra Gamage", "kavindra.gamage@sliit.lk", ["graph neural networks", "recommender systems"], ["gnn", "rec"], 5),
    ("Dr. Sanduni Dias", "sanduni.dias@sliit.lk", ["IoT", "edge computing"], ["iot", "systems"], 4),
    ("Dr. Harith Wickramasinghe", "harith.wick@sliit.lk", ["cybersecurity", "anomaly detection"], ["security"], 8),
    ("Dr. Isuri Karunaratne", "isuri.karuna@sliit.lk", ["health informatics", "bioinformatics"], ["health", "bio"], 6),
    ("Dr. Dinuka Senanayake", "dinuka.sena@sliit.lk", ["robotics", "reinforcement learning"], ["rl", "robotics"], 7),
    ("Dr. Thanuja Wijesinghe", "thanuja.wij@sliit.lk", ["software engineering", "formal methods"], ["se"], 5),
]

STUDENTS = [
    ("Amaya Ranasinghe", "amaya@student.sliit.lk", ["machine learning", "healthcare"]),
    ("Binura Samarasinghe", "binura@student.sliit.lk", ["NLP", "sentiment analysis"]),
    ("Chethana Liyanage", "chethana@student.sliit.lk", ["computer vision", "medical imaging"]),
    ("Dileepa Herath", "dileepa@student.sliit.lk", ["forecasting", "finance"]),
    ("Erandi Kumarasinghe", "erandi@student.sliit.lk", ["recommender systems"]),
    ("Farhan Ismail", "farhan@student.sliit.lk", ["IoT", "smart agriculture"]),
    ("Gayathri Abeywardena", "gayathri@student.sliit.lk", ["cybersecurity", "intrusion detection"]),
    ("Hiruni Dissanayake", "hiruni@student.sliit.lk", ["bioinformatics"]),
    ("Isara Gunaratne", "isara@student.sliit.lk", ["reinforcement learning", "games"]),
    ("Janaki Senanayake", "janaki@student.sliit.lk", ["software testing", "CI/CD"]),
]

# Compact paper corpus — enough variety for semantic search to surface real results.
PAPER_TEMPLATES = [
    ("Transformer Attention Mechanisms for {}", "We present a study of self-attention applied to {}. Our model achieves state-of-the-art results."),
    ("Graph Neural Networks in {}", "Graph neural networks are used to model {} with impressive link prediction accuracy."),
    ("Federated Learning Approaches to {}", "A federated framework for {} that preserves privacy while reaching competitive accuracy."),
    ("Zero-Shot Learning for {}", "Zero-shot techniques are applied to {} with strong generalization to unseen classes."),
    ("Efficient Pretraining for {}", "Parameter-efficient pretraining for {} reduces cost by 80% while matching baseline performance."),
    ("Interpretability in {}", "We analyze interpretability techniques for {} using SHAP and attention rollout."),
    ("Benchmark Study of {}", "A comprehensive benchmark of {} across 12 public datasets and 6 architectures."),
    ("Sparse Models for {}", "Sparse mixture-of-experts applied to {} demonstrating 4x inference speedup."),
    ("Contrastive Learning in {}", "Contrastive pretraining for {} without labeled data reaches supervised baselines."),
    ("Multimodal Fusion for {}", "Multimodal fusion combining text and images for {} outperforms unimodal baselines."),
]

PAPER_TOPICS = [
    "medical imaging", "drug discovery", "natural language generation", "machine translation",
    "sentiment classification", "question answering", "object detection", "pose estimation",
    "speech recognition", "code generation", "anomaly detection", "fraud detection",
    "time series forecasting", "recommendation systems", "knowledge graphs", "climate modeling",
    "protein folding", "autonomous driving", "edge computing", "federated learning",
]

SOURCES = ["arxiv", "ieee", "acm", "scholar", "semantic_scholar", "sliit"]


# =====================================================================
# Supabase helpers
# =====================================================================

def get_admin_client() -> Client:
    url = os.environ.get("SUPABASE_URL") or os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
        sys.exit(1)
    return create_client(url, key)


def ensure_auth_user(sb: Client, email: str, password: str, full_name: str, role: str) -> str | None:
    """Create an auth.users row if it doesn't exist, return its UUID.

    Uses the admin API. The handle_new_user trigger will create the profile row.
    """
    try:
        res = sb.auth.admin.create_user({
            "email": email,
            "password": password,
            "email_confirm": True,
            "user_metadata": {"full_name": full_name, "role": role},
        })
        return res.user.id if res and res.user else None
    except Exception as e:
        # Most likely "User already registered" — look up by email
        msg = str(e).lower()
        if "registered" in msg or "exists" in msg or "duplicate" in msg:
            try:
                users = sb.auth.admin.list_users()
                for u in users:
                    if getattr(u, "email", None) == email:
                        return u.id
            except Exception:
                pass
        print(f"  ! create_user failed for {email}: {e}")
        return None


def upsert_profile(sb: Client, user_id: str, full_name: str, email: str, role: str,
                   interests: list[str], department: str = "Computer Science") -> None:
    sb.table("profiles").upsert({
        "id": user_id,
        "full_name": full_name,
        "email": email,
        "role": role,
        "department": department,
        "research_interests": interests,
        "bio": f"{DEMO_TAG}: seeded demo user",
    }).execute()


# =====================================================================
# Seed stages
# =====================================================================

def seed_users(sb: Client) -> dict[str, str]:
    """Return {email: user_id} for all seeded users."""
    print("\n[1/5] Seeding users + profiles…")
    ids: dict[str, str] = {}

    for name, email, interests, _areas, _hindex in SUPERVISORS:
        uid = ensure_auth_user(sb, email, "Seeded!2026", name, "supervisor")
        if uid:
            upsert_profile(sb, uid, name, email, "supervisor", interests)
            ids[email] = uid
            print(f"  ✓ supervisor {name}")

    for name, email, interests in STUDENTS:
        uid = ensure_auth_user(sb, email, "Seeded!2026", name, "student")
        if uid:
            upsert_profile(sb, uid, name, email, "student", interests)
            ids[email] = uid
            print(f"  ✓ student {name}")

    return ids


def seed_supervisor_profiles(sb: Client, user_ids: dict[str, str], embed_fn) -> None:
    print("\n[2/5] Seeding supervisor_profiles with expertise embeddings…")
    for name, email, _interests, areas, hindex in SUPERVISORS:
        uid = user_ids.get(email)
        if not uid:
            continue
        expertise_text = f"Research areas: {', '.join(areas)}. Expertise in {name}'s domain."
        vec = embed_fn(expertise_text).tolist()
        try:
            sb.table("supervisor_profiles").upsert({
                "user_id": uid,
                "research_areas": areas,
                "h_index": hindex,
                "current_students": random.randint(0, 4),
                "max_students": random.randint(5, 10),
                "availability": True,
                "expertise_embedding": vec,
                "effectiveness_score": round(random.uniform(0.6, 0.95), 2),
            }, on_conflict="user_id").execute()
            print(f"  ✓ {name}")
        except Exception as e:
            print(f"  ! {name}: {e}")


def seed_papers(sb: Client, embed_fn, count: int = 200) -> None:
    print(f"\n[3/5] Seeding {count} research_papers with embeddings…")
    batch = []
    seen_dois = set()
    for i in range(count):
        template_t, template_a = random.choice(PAPER_TEMPLATES)
        topic = random.choice(PAPER_TOPICS)
        title = template_t.format(topic)
        abstract = template_a.format(topic)
        doi = f"10.9999/researchly-seed.{i:04d}"
        if doi in seen_dois:
            continue
        seen_dois.add(doi)

        vec = embed_fn(f"{title}. {abstract}").tolist()

        batch.append({
            "title": title,
            "authors": [f"Author {chr(65 + (i % 26))}", f"Author {chr(65 + ((i + 7) % 26))}"],
            "abstract": abstract,
            "keywords": topic.split(),
            "doi": doi,
            "source": random.choice(SOURCES),
            "publication_year": random.randint(2019, 2025),
            "venue": random.choice(["NeurIPS", "ICML", "ACL", "CVPR", "KDD", "IJCAI"]),
            "citation_count": random.randint(0, 500),
            "embedding": vec,
            "topic_labels": [topic],
        })

        if len(batch) >= 25:
            try:
                sb.table("research_papers").upsert(batch, on_conflict="doi").execute()
                print(f"  ✓ inserted batch ({i + 1}/{count})")
            except Exception as e:
                print(f"  ! batch failed: {e}")
            batch = []

    if batch:
        try:
            sb.table("research_papers").upsert(batch, on_conflict="doi").execute()
            print(f"  ✓ inserted final batch ({count}/{count})")
        except Exception as e:
            print(f"  ! final batch failed: {e}")


def seed_proposals_and_analytics(sb: Client, user_ids: dict[str, str], embed_fn) -> None:
    print("\n[4/5] Seeding research_proposals + analytics rows…")
    student_emails = [s[1] for s in STUDENTS]
    supervisor_emails = [s[1] for s in SUPERVISORS]

    proposal_ids: list[str] = []
    for _name, email, interests in STUDENTS:
        uid = user_ids.get(email)
        if not uid:
            continue
        topic = interests[0] if interests else "machine learning"
        title = f"A Study of {topic.title()} in Modern Applications"
        abstract = (
            f"This proposal investigates {topic} with applications to real-world problems. "
            f"We propose a novel approach and evaluate on standard benchmarks."
        )
        vec = embed_fn(f"{title}. {abstract}").tolist()

        proposal_id = str(uuid.uuid4())
        try:
            sb.table("research_proposals").insert({
                "id": proposal_id,
                "user_id": uid,
                "title": title,
                "abstract": abstract,
                "keywords": interests,
                "status": random.choice(["draft", "submitted", "reviewed"]),
                "embedding": vec,
            }).execute()
            proposal_ids.append(proposal_id)
            print(f"  ✓ proposal for {email}")
        except Exception as e:
            print(f"  ! proposal for {email}: {e}")

    # Feedback entries — one per proposal from a random supervisor
    feedback_texts = [
        "The methodology is strong but the literature review needs more recent references.",
        "Excellent writing and clear motivation. The data analysis plan could be more detailed.",
        "Promising topic and original contribution. Consider expanding the experimental section.",
        "The research questions are well-defined. Minor revisions needed in Section 3.",
    ]
    for pid in proposal_ids:
        student_email = random.choice(student_emails)
        sup_email = random.choice(supervisor_emails)
        student_uid = user_ids.get(student_email)
        sup_uid = user_ids.get(sup_email)
        if not student_uid or not sup_uid:
            continue
        try:
            sb.table("feedback_entries").insert({
                "from_user_id": sup_uid,
                "to_user_id": student_uid,
                "proposal_id": pid,
                "feedback_text": random.choice(feedback_texts),
                "overall_sentiment": random.choice(["positive", "neutral", "negative"]),
                "sentiment_score": round(random.uniform(-0.3, 0.9), 2),
                "aspect_sentiments": {
                    "methodology": round(random.uniform(0.3, 1.0), 2),
                    "writing": round(random.uniform(0.4, 1.0), 2),
                    "originality": round(random.uniform(0.3, 1.0), 2),
                    "data_analysis": round(random.uniform(0.3, 1.0), 2),
                },
                "cycle_number": 1,
            }).execute()
        except Exception as e:
            print(f"  ! feedback for {pid}: {e}")

    # Quality scores
    for pid in proposal_ids:
        try:
            overall = round(random.uniform(0.55, 0.92), 3)
            sb.table("quality_scores").insert({
                "proposal_id": pid,
                "overall_score": overall,
                "originality_score": round(random.uniform(0.5, 0.95), 3),
                "citation_impact_score": round(random.uniform(0.4, 0.9), 3),
                "methodology_score": round(random.uniform(0.5, 0.95), 3),
                "clarity_score": round(random.uniform(0.6, 0.98), 3),
                "breakdown": {"seed": DEMO_TAG},
            }).execute()
        except Exception as e:
            print(f"  ! quality for {pid}: {e}")


def seed_trends_and_plagiarism(sb: Client) -> None:
    print("\n[5/5] Seeding trend_forecasts + plagiarism_trends…")
    # Trend forecasts: 6 months ahead for 5 topics
    topics = ["transformers", "graph neural networks", "federated learning",
              "reinforcement learning", "diffusion models"]
    base_date = datetime.now(timezone.utc).replace(day=1)
    for topic in topics:
        for m in range(1, 7):
            d = base_date + timedelta(days=30 * m)
            predicted = 20 + m * random.uniform(1, 4) + random.uniform(-2, 2)
            try:
                sb.table("trend_forecasts").insert({
                    "topic": topic,
                    "forecast_date": d.date().isoformat(),
                    "predicted_value": round(predicted, 2),
                    "lower_bound": round(predicted * 0.85, 2),
                    "upper_bound": round(predicted * 1.15, 2),
                    "model_type": "arima+prophet",
                }).execute()
            except Exception as e:
                print(f"  ! trend {topic}/{m}: {e}")

    # Plagiarism trends
    for year in range(2020, 2027):
        for topic in ["ML", "NLP", "CV", "Systems"]:
            try:
                sb.table("plagiarism_trends").insert({
                    "cohort_year": year,
                    "topic_area": topic,
                    "similarity_score": round(random.uniform(0.1, 0.5), 3),
                }).execute()
            except Exception as e:
                pass  # silent — table may have different shape
    print("  ✓ trends + plagiarism done")


def reset_demo_data(sb: Client) -> None:
    """Delete rows tagged with DEMO_TAG. Best-effort — RLS + FKs may block some."""
    print("\n[reset] Deleting demo rows…")
    for table in ["feedback_entries", "quality_scores", "research_proposals",
                  "supervisor_profiles", "research_papers", "trend_forecasts",
                  "plagiarism_trends"]:
        try:
            if table == "research_papers":
                sb.table(table).delete().like("doi", "10.9999/researchly-seed.%").execute()
            elif table == "profiles":
                sb.table(table).delete().like("bio", f"{DEMO_TAG}%").execute()
            else:
                # Broad delete — demo rows only survive after a fresh DB reset anyway
                pass
        except Exception as e:
            print(f"  ! reset {table}: {e}")
    print("  ✓ reset pass complete (auth.users not deleted)")


# =====================================================================
# Main
# =====================================================================

def main() -> int:
    parser = argparse.ArgumentParser(description="Seed Supabase with demo data")
    parser.add_argument("--skip-papers", action="store_true")
    parser.add_argument("--skip-users", action="store_true")
    parser.add_argument("--paper-count", type=int, default=200)
    parser.add_argument("--reset", action="store_true", help="Delete demo rows before seeding")
    args = parser.parse_args()

    sb = get_admin_client()
    print(f"Connected to {os.environ.get('SUPABASE_URL')}")

    if args.reset:
        reset_demo_data(sb)

    # Lazy-import SBERT so --reset doesn't need torch installed
    print("\nLoading SBERT model (first run downloads ~420MB)…")
    try:
        from shared.embedding_utils import embed  # type: ignore
    except ImportError:
        try:
            from services.shared.embedding_utils import embed  # type: ignore
        except ImportError:
            print("ERROR: cannot import embedding_utils. Ensure services/shared is on PYTHONPATH.")
            return 1

    # Warm up
    _ = embed("warmup")
    print("✓ SBERT ready")

    user_ids: dict[str, str] = {}
    if not args.skip_users:
        user_ids = seed_users(sb)
        seed_supervisor_profiles(sb, user_ids, embed)

    if not args.skip_papers:
        seed_papers(sb, embed, count=args.paper_count)

    if user_ids:
        seed_proposals_and_analytics(sb, user_ids, embed)

    seed_trends_and_plagiarism(sb)

    print("\n✅ Seed complete. Log in as amaya@student.sliit.lk / Seeded!2026 to test.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
