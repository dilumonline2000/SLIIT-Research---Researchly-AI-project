import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "services"))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "services", ".env"))
from shared.supabase_client import get_supabase_admin

sb = get_supabase_admin()
tables = [
    "research_papers", "research_proposals", "research_summaries", "plagiarism_trends",
    "peer_groups", "peer_group_join_requests", "supervisor_ratings", "supervisor_matches",
    "quality_scores", "success_predictions", "profiles",
]
for t in tables:
    try:
        c = sb.table(t).select("id", count="exact").limit(1).execute().count
        print(f"{t}: {c} rows")
    except Exception as e:
        print(f"{t}: ERROR - {e}")
