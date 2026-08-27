import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "services"))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "services", ".env"))
from shared.supabase_client import get_supabase_admin

sb = get_supabase_admin()
total = sb.table("research_papers").select("id", count="exact").execute().count
with_emb = sb.table("research_papers").select("id", count="exact").not_.is_("embedding", "null").execute().count
print(f"research_papers total: {total}")
print(f"research_papers with non-null embedding: {with_emb}")
