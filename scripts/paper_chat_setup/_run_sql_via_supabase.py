"""Execute SQL migration files against Supabase using the REST API.

Uses the service_role key to call the pg_net / exec_sql RPC if available,
falling back to splitting the SQL into individual statements and running
each via supabase-py's .rpc() mechanism.
Reads credentials from services/.env or environment variables.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

MIGRATIONS = [
    ROOT / "supabase" / "migrations" / "009_paper_uploads.sql",
    ROOT / "supabase" / "migrations" / "010_chat_tables.sql",
    ROOT / "supabase" / "migrations" / "011_training_data.sql",
]


def _load_env() -> dict:
    env: dict = {}
    env_file = ROOT / "services" / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    for k in ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"):
        if os.environ.get(k):
            env[k] = os.environ[k]
    return env


def _split_statements(sql: str) -> list[str]:
    """Split SQL on semicolons, skipping PL/pgSQL bodies ($$...$$)."""
    stmts = []
    current: list[str] = []
    in_dollar = False
    for line in sql.splitlines():
        stripped = line.strip()
        if "$$" in stripped:
            in_dollar = not in_dollar
        current.append(line)
        if not in_dollar and stripped.endswith(";"):
            stmt = "\n".join(current).strip()
            if stmt:
                stmts.append(stmt)
            current = []
    leftover = "\n".join(current).strip()
    if leftover:
        stmts.append(leftover)
    return [s for s in stmts if s and not re.match(r"^--", s)]


def run() -> int:
    env = _load_env()
    url = env.get("SUPABASE_URL", "")
    key = env.get("SUPABASE_SERVICE_ROLE_KEY", "")

    if not url or not key:
        print("[!] SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY not set")
        return 1

    from supabase import create_client

    sb = create_client(url, key)

    for mig_file in MIGRATIONS:
        print(f"\n>>> {mig_file.name}")
        sql = mig_file.read_text(encoding="utf-8")

        # Try exec_sql RPC (available when pg_net / custom function is installed)
        try:
            sb.rpc("exec_sql", {"sql": sql}).execute()
            print(f"    [OK] applied via exec_sql RPC")
            continue
        except Exception:
            pass

        # Fallback: POST directly to the Postgres REST API using service_role
        import urllib.request
        import json

        api_url = url.rstrip("/") + "/rest/v1/rpc/exec_sql"
        headers = {
            "Authorization": f"Bearer {key}",
            "apikey": key,
            "Content-Type": "application/json",
        }
        body = json.dumps({"sql": sql}).encode()
        req = urllib.request.Request(api_url, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                print(f"    [OK] applied via REST RPC ({r.status})")
            continue
        except Exception as e:
            print(f"    exec_sql not available ({e}), trying statement-by-statement...")

        # Final fallback: split and run each CREATE/INSERT etc individually.
        # Supabase REST doesn't expose arbitrary SQL to clients, so we use
        # the Management API instead.
        proj_ref = url.split("//")[1].split(".")[0]
        mgmt_url = f"https://api.supabase.com/v1/projects/{proj_ref}/database/query"
        body = json.dumps({"query": sql}).encode()
        mgmt_req = urllib.request.Request(
            mgmt_url,
            data=body,
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(mgmt_req, timeout=60) as r:
                print(f"    [OK] applied via Management API ({r.status})")
            continue
        except Exception as e:
            print(f"    Management API also failed: {e}")
            print("    Please paste scripts/paper_chat_setup/all_new_migrations.sql")
            print("    into the Supabase SQL editor manually.")
            return 2

    print("\n[OK] All migrations applied successfully")
    return 0


if __name__ == "__main__":
    sys.exit(run())
