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

# Try the match_papers RPC directly with a real embedding from module1's SBERT model to see if it returns anything at low threshold
from sentence_transformers import SentenceTransformer
model_dir = os.path.join(os.path.dirname(__file__), "..", "..", "services", "module1-integrity", "models", "sbert_plagiarism")
m = SentenceTransformer(model_dir if os.path.exists(os.path.join(model_dir, "model.safetensors")) else "sentence-transformers/all-MiniLM-L6-v2")
vec = m.encode("Machine learning models such as convolutional neural networks have been widely used for image classification tasks in recent research, achieving high accuracy on benchmark datasets.", normalize_embeddings=True).tolist()
res = sb.rpc("match_papers", {"query_embedding": vec, "match_count": 3, "match_threshold": 0.0}).execute()
print("match_papers @ threshold=0.0 ->", len(res.data or []), "rows")
for r in (res.data or [])[:3]:
    print("  ", round(r.get("similarity", 0), 4), "-", (r.get("title") or "")[:80])
