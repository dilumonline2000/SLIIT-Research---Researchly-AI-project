"""Create the `research-papers` Supabase Storage bucket.

Usage (from repo root):
    python scripts/paper_chat_setup/create_storage_bucket.py

Reads SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY from services/.env
(or the current environment). Uses the HTTP API directly so it works
without the supabase-py package installed.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from urllib import request as _urlreq, error as _urlerr
import json as _json

BUCKET = "research-papers"
ROOT = Path(__file__).resolve().parents[2]


def _load_env() -> dict:
    env: dict[str, str] = {}
    env_file = ROOT / "services" / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    # Process env wins
    for k in ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"):
        if k in os.environ and os.environ[k]:
            env[k] = os.environ[k]
    return env


def main() -> int:
    env = _load_env()
    url = env.get("SUPABASE_URL", "")
    key = env.get("SUPABASE_SERVICE_ROLE_KEY", "")

    if not url or "REPLACE_WITH" in key or not key:
        print("[!] SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY not set in services/.env")
        print("    Fill in real values from Supabase Settings -> API, then retry.")
        return 1

    base = url.rstrip("/") + "/storage/v1/bucket"
    headers = {
        "Authorization": f"Bearer {key}",
        "apikey": key,
        "Content-Type": "application/json",
    }

    def _req(method: str, path: str, body: dict | None = None) -> tuple[int, str]:
        data = _json.dumps(body).encode() if body is not None else None
        req = _urlreq.Request(path, data=data, headers=headers, method=method)
        try:
            with _urlreq.urlopen(req, timeout=15) as resp:
                return resp.status, resp.read().decode("utf-8", "ignore")
        except _urlerr.HTTPError as e:
            return e.code, e.read().decode("utf-8", "ignore")
        except Exception as e:
            return 0, str(e)

    status, body = _req("GET", f"{base}/{BUCKET}")
    if status == 200:
        print(f"[OK] bucket '{BUCKET}' already exists")
        return 0

    payload = {
        "id": BUCKET,
        "name": BUCKET,
        "public": True,
        "file_size_limit": 50 * 1024 * 1024,
        "allowed_mime_types": ["application/pdf"],
    }
    status, body = _req("POST", base, payload)
    if status in (200, 201):
        print(f"[OK] created bucket '{BUCKET}' (public, 50MB limit, pdf only)")
        return 0
    print(f"[FAIL] failed: {status} {body}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
