"""Run the three new paper-chat migrations against your Supabase Postgres.

Usage (from repo root):
    export SUPABASE_DB_URL="postgres://postgres:<DB_PASSWORD>@db.<ref>.supabase.co:5432/postgres"
    python scripts/paper_chat_setup/run_migrations.py

Find SUPABASE_DB_URL in Supabase: Settings → Database → Connection string (URI).

If you'd rather not install psycopg locally, just open the SQL editor and
paste scripts/paper_chat_setup/all_new_migrations.sql instead.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FILES = [
    ROOT / "supabase" / "migrations" / "009_paper_uploads.sql",
    ROOT / "supabase" / "migrations" / "010_chat_tables.sql",
    ROOT / "supabase" / "migrations" / "011_training_data.sql",
]


def main() -> int:
    db_url = os.environ.get("SUPABASE_DB_URL") or os.environ.get("DATABASE_URL")
    if not db_url:
        print("[!] SUPABASE_DB_URL is not set.")
        print("    Get it from: Supabase -> Settings -> Database -> Connection string (URI)")
        print("    Or paste scripts/paper_chat_setup/all_new_migrations.sql into the SQL editor.")
        return 1

    try:
        import psycopg  # type: ignore
    except ImportError:
        print("[!] psycopg not installed. Run: pip install 'psycopg[binary]'")
        print("    Alternative: paste all_new_migrations.sql into Supabase SQL editor.")
        return 2

    conn = psycopg.connect(db_url, autocommit=True)
    try:
        with conn.cursor() as cur:
            for f in FILES:
                print(f"→ applying {f.name}")
                sql = f.read_text(encoding="utf-8")
                cur.execute(sql)
                print(f"  [OK] {f.name}")
    finally:
        conn.close()

    print("[OK] all paper-chat migrations applied")
    return 0


if __name__ == "__main__":
    sys.exit(main())
