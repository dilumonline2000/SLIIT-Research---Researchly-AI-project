"""
Upload fine-tuned SBERT supervisor embeddings to Supabase pgvector.

Run:
    python training/upload_to_supabase.py

Requires .env with:
    SUPABASE_URL=https://your-supabase-project.supabase.co
    SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
"""

import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from tqdm import tqdm

# Load .env from the root of the monorepo
ENV_FILE = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(ENV_FILE)

# Import Supabase client from shared services
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from shared.supabase_client import get_supabase_admin

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
EMB_FILE = DATA_DIR / "supervisors_with_embeddings.json"


def upload():
    print("\n" + "=" * 70)
    print("  UPLOADING SUPERVISOR EMBEDDINGS -> SUPABASE")
    print("=" * 70 + "\n")

    # Load supervisors with embeddings
    with open(EMB_FILE, encoding="utf-8") as f:
        supervisors = json.load(f)

    print(f"[*] {len(supervisors)} supervisors to upload\n")

    supabase = get_supabase_admin()

    success_count = 0
    error_count = 0
    errors = []

    for sup in tqdm(supervisors, desc="Uploading"):
        if not sup.get("embedding"):
            print(f"  [!] Skipping {sup['name']} - no embedding")
            continue

        # Map to Supabase supervisor_profiles table schema
        # Only include fields that exist in the table to avoid schema cache errors
        payload = {
            "email": sup["email"],
            # SBERT embedding (384-dim for all-MiniLM-L6-v2)
            "expertise_embedding": sup["embedding"],
            # Metadata
            "embedding_text": sup.get("embedding_text", ""),
            "model_version": "sbert-v1-finetuned-r26it116",
        }

        try:
            # Upsert on email (unique identifier)
            result = (
                supabase.table("supervisor_profiles")
                .upsert(payload, on_conflict="email")
                .execute()
            )
            success_count += 1

        except Exception as e:
            error_count += 1
            errors.append({"supervisor": sup["name"], "error": str(e)})
            print(f"\n  [!] Error uploading {sup['name']}: {e}")

    print(f"\n{'=' * 70}")
    print(f"  [+] Successfully uploaded: {success_count}")
    print(f"  [!] Errors:             {error_count}")

    if errors:
        print("\n  Errors detail:")
        for e in errors:
            print(f"    - {e['supervisor']}: {e['error']}")

    # Verify upload
    print("\n[+] Verifying upload...")
    try:
        count_result = (
            supabase.table("supervisor_profiles")
            .select("id", count="exact")
            .execute()
        )
        print(f"  Total supervisors in Supabase: {count_result.count}")
    except Exception as e:
        print(f"  [!] Could not verify count: {e}")

    print(f"\n[+] Upload complete!\n")


if __name__ == "__main__":
    upload()
